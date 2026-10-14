"""Verify, reproduce or retrain the binary-pair coverage study in Fig. 3/Table S2."""
from pathlib import Path
import argparse,csv,hashlib,json,sys
from itertools import combinations
import numpy as np

STUDY=Path(__file__).resolve().parents[1]
ROOT=STUDY.parents[3]
sys.path.insert(0,str(ROOT/'src'))
from thermoformer.data import load_vle_dataset,retain_pure_anchored_systems
from thermoformer.data.splitting import sample_id,canonical_smiles,dataset_digest
from thermoformer.evaluation.prediction import _metrics_for_group

TASKS=[('Isothermal P','isothermal','pressure_r2'),('Isothermal y','isothermal','y_r2'),('Isobaric T','isobaric','temperature_r2'),('Isobaric y','isobaric','y_r2')]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read_json(p):return json.loads(p.read_text(encoding='utf-8'))
def write_json(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2),encoding='utf-8')
def read_csv(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write_csv(p,rows):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def predictions(p):
    rows=read_csv(p)
    for r in rows:
        for k,v in list(r.items()):
            if v=='':r[k]=None
            elif v in ('True','False'):r[k]=v=='True'
            elif k=='component_count':r[k]=int(v)
    return rows
def load_samples():
    return retain_pure_anchored_systems(load_vle_dataset(ROOT/'datasets/vle',failed_weight=0,max_pressure_kpa=500).samples,minimum_temperatures=2)
def system(s):return tuple(sorted(map(canonical_smiles,s.smiles)))
def pairs(s):return set(combinations(system(s),2))

def summarize(results):
    rows={(s,k):predictions(results/f'seed_{s}/coverage_{k}/predictions.csv') for s in range(5) for k in range(4)}
    identities=[{(r['sample_id'],r['direction']) for r in rr} for rr in rows.values()]
    if not all(x==identities[0] for x in identities):raise ValueError('Different test samples across runs')
    common=set.intersection(*({(r['sample_id'],r['direction']) for r in rr if r['converged'] and not r['nonphysical']} for rr in rows.values()))
    per_seed=[];summary=[]
    for task,direction,key in TASKS:
        for k in range(4):
            values=[]
            for s in range(5):
                subset=[r for r in rows[s,k] if r['direction']==direction and (r['sample_id'],direction) in common]
                metric=_metrics_for_group(subset,'paired',direction,3)
                values.append(metric[key]);per_seed.append({'task':task,'covered_pairs':k,'seed':s,'R2':metric[key],'evaluated':len(subset)})
            if any(v is None for v in values):raise ValueError('Undefined R2 in paired test subset')
            summary.append({'task':task,'covered_pairs':k,'R2_mean':float(np.mean(values)),'R2_sample_sd':float(np.std(values,ddof=1)),'seeds':5,'evaluated_points_per_seed':len(subset)})
    return summary,per_seed,len(common)

def verify():
    manifest=read_json(STUDY/'artifact_manifest.json')
    for relative,digest in manifest['sha256'].items():
        if sha(STUDY/relative)!=digest:raise ValueError('Artifact digest mismatch: '+relative)
    samples=load_samples();lookup={sample_id(s):s for s in samples}
    design=read_json(STUDY/'design.json')
    if dataset_digest(samples)!=design['dataset_sha256']:raise ValueError('Dataset identity mismatch')
    targets=[tuple(t) for t in design['eligible_target_systems']]
    edges=set(p for t in targets for p in combinations(t,2))
    fixed_test=fixed_val=fixed_molecules=None
    for s in range(5):
        previous=set();initial=[]
        for k in range(4):
            split_path=STUDY/f'splits/coverage_{k}_seed_{s}.json'
            pp=read_json(split_path)['partitions'];train=[lookup[i] for i in pp['train']]
            validation=[lookup[i] for i in pp['validation']];test=[lookup[i] for i in pp['test']]
            if len(train)!=8238 or len(validation)!=1303 or len(test)!=517:raise ValueError('Incorrect partition sizes')
            if sum(len(r.smiles)==2 for r in train)!=7595:raise ValueError('Binary training count mismatch')
            if set(pp['train'])&set(pp['validation']+pp['test']):raise ValueError('Overlapping sample IDs')
            if {system(r) for r in train}&{system(r) for r in validation+test}:raise ValueError('Overlapping systems')
            observed=set().union(*(pairs(r) for r in train))
            if any(len(set(combinations(t,2))&observed)!=k for t in targets):raise ValueError('Incorrect pair coverage')
            if set().union(*(pairs(r) for r in validation))&edges:raise ValueError('Target pair in validation')
            selected={sample_id(r) for r in train if pairs(r)&edges}
            if not previous<=selected:raise ValueError('Non-nested intervention')
            previous=selected;molecules={m for r in train for m in system(r)}
            if fixed_test is None:fixed_test=pp['test'];fixed_val=pp['validation'];fixed_molecules=molecules
            if fixed_test!=pp['test'] or fixed_val!=pp['validation'] or fixed_molecules!=molecules:raise ValueError('Fixed controls differ')
            if not {m for t in targets for m in t}<=molecules:raise ValueError('Unseen test molecule')
            selection=read_json(STUDY/f'results/seed_{s}/coverage_{k}/selection.json')
            if selection['split_sha256']!=sha(split_path):raise ValueError('Selection/split digest mismatch')
            initial.append(selection['initial_state_sha256'])
            if selection['selected_stage']!=min(selection['validation_scores'],key=selection['validation_scores'].get):raise ValueError('Checkpoint selection mismatch')
        if len(set(initial))!=1:raise ValueError('Unpaired initialization')
    summary,per_seed,n=summarize(STUDY/'results')
    if n!=517:raise ValueError('Reference prediction validity differs')
    reference=read_csv(STUDY/'results/R2_summary.csv')
    for row in summary:
        expected=next(r for r in reference if r['task']==row['task'] and int(r['covered_pairs'])==row['covered_pairs'])
        for key in ['R2_mean','R2_sample_sd']:
            if not np.isclose(row[key],float(expected[key]),rtol=0,atol=1e-12):raise ValueError('Table S2 differs')
    print('PASS: artifact hashes, 20 paired splits, molecular exposure, selection, 517 test points and Table S2.')

def report(output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    summary,per_seed,n=summarize(STUDY/'results')
    output.mkdir(parents=True,exist_ok=True)
    write_csv(output/'R2_summary.csv',summary);write_csv(output/'per_seed_R2.csv',per_seed)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
    fig,axs=plt.subplots(2,2,figsize=(7,4.7))
    for ax,(task,_,_),color,letter in zip(axs.flat,TASKS,['#0072B2','#009E73','#D55E00','#CC79A7'],'ijkl'):
        rr=[r for r in summary if r['task']==task]
        ax.bar(range(4),[r['R2_mean'] for r in rr],width=.6,color=color,yerr=[r['R2_sample_sd'] for r in rr],capsize=3,error_kw={'elinewidth':.8})
        ax.set_xticks(range(4));ax.set_xlabel('Binary pairs covered in training');ax.set_ylabel(r'$R^2$')
        ax.set_title(task,loc='left');ax.text(-.15,1.04,letter,transform=ax.transAxes,fontweight='bold')
        ax.axhline(1,ls=':',lw=.7,color='gray');ax.set_ylim(0,1.08)
    fig.tight_layout();fig.savefig(output/'controlled_R2.svg');fig.savefig(output/'controlled_R2.png',dpi=300)
    print(f'Recomputed Table S2 and panels i-l on {n} shared test points: {output}')

def model_action(args):
    import torch
    from thermoformer.models import ThermoFormer,ThermoFormerConfig
    from thermoformer.training import TrainingConfig,fit_model,seed_everything
    from thermoformer.training.direct_ge_pipeline import fit_direct_ge_stages
    from thermoformer.configuration import DirectGESupervisionConfig,PhysicsFineTuningConfig
    from thermoformer.features import feature_subset_sha256
    from thermoformer.evaluation import predict_vle,write_prediction_csv
    from thermoformer.thermodynamics.vapor_pressure import load_pure_property_catalog
    torch.set_num_threads(4)
    device=torch.device(args.device)
    if device.type=='cuda' and not torch.cuda.is_available():raise RuntimeError('CUDA unavailable')
    samples=load_samples();lookup={sample_id(s):s for s in samples}
    if dataset_digest(samples)!=read_json(STUDY/'design.json')['dataset_sha256']:raise ValueError('Dataset mismatch')
    with np.load(STUDY/'features/prepared_features.npz',allow_pickle=False) as f:features=dict(zip(f['smiles'].astype(str),f['features']))
    if feature_subset_sha256(features)!=read_json(STUDY/'features/metadata.json')['feature_subset_sha256']:raise ValueError('Feature mismatch')
    provenance=read_json(STUDY/'provenance.json')
    catalog_path=ROOT/'datasets/derived/thermodynamic_labels/external_psat_catalog.json'
    if sha(catalog_path)!=provenance['catalog_sha256']:raise ValueError('Pure-property catalog mismatch')
    catalog=load_pure_property_catalog(catalog_path)
    for seed in args.seeds:
        for k in args.coverages:
            output=args.output_dir/f'seed_{seed}'/f'coverage_{k}'
            output.mkdir(parents=True,exist_ok=False)
            config=read_json(STUDY/f'results/seed_{seed}/coverage_{k}/resolved_config.json')
            pp=read_json(STUDY/f'splits/coverage_{k}_seed_{seed}.json')['partitions']
            train,val,test=([lookup[i] for i in pp[name]] for name in ['train','validation','test'])
            seed_everything(seed);model=ThermoFormer(ThermoFormerConfig(**config['model']))
            tc=TrainingConfig(**config['training'])
            if args.command=='train':
                init=hashlib.sha256(b''.join(v.detach().cpu().numpy().tobytes() for v in model.state_dict().values())).hexdigest()
                baseline=fit_model(model,train,features,tc,device,validation_samples=val,pure_property_catalog=catalog)
                result=fit_direct_ge_stages(model,train,features,tc,DirectGESupervisionConfig(**config['direct_ge_supervision']),PhysicsFineTuningConfig(**config['physics_finetuning']),device,validation_samples=val,pure_property_catalog=catalog,baseline_state=baseline.state_dict)
                selection={'selected_stage':result.selected_stage,'validation_scores':result.stage_validation_losses,'initial_state_sha256':init}
                write_json(output/'selection.json',selection)
                torch.save({'state_dict':result.state_dict,'model_config':config['model'],'selection':selection},output/'best_model.pt')
            else:
                checkpoint=torch.load(STUDY/f'checkpoints/seed_{seed}/coverage_{k}.pt',map_location='cpu',weights_only=False)
                model.load_state_dict(checkpoint['state_dict'])
            model.to(device)
            rr=predict_vle(model,test,features,batch_size=tc.batch_size,device=device,solver_iterations=tc.solver_iterations_eval,pure_property_catalog=catalog)
            write_prediction_csv(output/'predictions.csv',rr)
            print(f'{args.command}: seed={seed}, coverage={k}, predictions={len(rr)}')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['verify','report','predict','train'])
    parser.add_argument('--output-dir',type=Path)
    parser.add_argument('--seeds',nargs='+',type=int,default=list(range(5)),choices=range(5))
    parser.add_argument('--coverages',nargs='+',type=int,default=list(range(4)),choices=range(4))
    parser.add_argument('--device',choices=['cpu','cuda'],default='cuda')
    args=parser.parse_args()
    if args.command=='verify':verify();return
    if args.output_dir is None:parser.error('--output-dir is required')
    args.output_dir=args.output_dir.resolve()
    if args.output_dir==STUDY or STUDY in args.output_dir.parents:parser.error('Use an output directory outside the archived study')
    if args.command=='report':report(args.output_dir)
    else:model_action(args)

if __name__=='__main__':main()
