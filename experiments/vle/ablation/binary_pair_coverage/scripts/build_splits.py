"""Outcome-blind paired coverage intervention; no archived checkpoints reused."""
from pathlib import Path
import sys, json, random, csv
from collections import defaultdict, Counter
from itertools import combinations, permutations

STUDY=Path(__file__).resolve().parent.parent
OUT=STUDY
ROOT=STUDY.parents[3]
sys.path.insert(0,str(ROOT/'src'))
from thermoformer.data import load_vle_dataset, retain_pure_anchored_systems
from thermoformer.data.splitting import canonical_smiles, sample_id, dataset_digest

def system(s): return tuple(sorted(map(canonical_smiles,s.smiles)))
def pairs(s): return set(combinations(system(s),2))
def load():
    return retain_pure_anchored_systems(load_vle_dataset(ROOT/'datasets/vle',failed_weight=0,max_pressure_kpa=500).samples,minimum_temperatures=2)

def color_edges(triples):
    neighbors=defaultdict(set)
    for tri in triples:
        pp=list(combinations(tri,2))
        for p in pp: neighbors[p].update(set(pp)-{p})
    assignment={}
    def solve():
        if len(assignment)==len(neighbors): return True
        p=max((p for p in neighbors if p not in assignment),key=lambda p:(len({assignment[q] for q in neighbors[p] if q in assignment}),len(neighbors[p]),p))
        forbidden={assignment[q] for q in neighbors[p] if q in assignment}
        for c in range(3):
            if c not in forbidden:
                assignment[p]=c
                if solve(): return True
                del assignment[p]
        return False
    if not solve(): raise ValueError('Target pair graph is not three-colorable; requires another prespecified design.')
    return assignment

def main():
    samples=load(); bysys=defaultdict(list)
    for s in samples: bysys[system(s)].append(s)
    eligible=sorted(t for t in bysys if len(t)==3 and all(p in bysys for p in combinations(t,2)))
    initial_candidates=list(eligible)
    target_pairs=set(p for t in eligible for p in combinations(t,2))
    background_molecules={m for s in samples if not pairs(s)&target_pairs for m in system(s)}
    excluded=[{'system':t,'missing_background_molecules':sorted(set(t)-background_molecules)} for t in eligible if set(t)-background_molecules]
    eligible=[t for t in eligible if not set(t)-background_molecules]
    colors=color_edges(eligible); target_pairs=set(colors)
    test=[s for s in samples if system(s) in eligible]
    background=[s for s in samples if not (pairs(s)&target_pairs) and system(s) not in eligible]
    # Fixed system-level validation, independent of outcomes and intervention seed.
    rng=random.Random(20260922)
    val_systems=set()
    for order in (2,3):
        systems=sorted({system(s) for s in background if len(s.smiles)==order})
        rng.shuffle(systems)
        val_systems.update(systems[:max(1,round(.15*len(systems)))])
    validation=[s for s in background if system(s) in val_systems]
    # Preserve molecule exposure if the validation draw removes a target molecule.
    required_molecules={m for t in eligible for m in t}
    for molecule in sorted(required_molecules):
        if not any(molecule in system(s) for s in background if system(s) not in val_systems):
            candidate=min(system(s) for s in background if molecule in system(s))
            val_systems.discard(candidate)
    validation=[s for s in background if system(s) in val_systems]
    bg=[s for s in background if system(s) not in val_systems]
    binary=[s for s in bg if len(s.smiles)==2]
    fixed=[s for s in bg if len(s.smiles)!=2]
    # Allocate <=20 observations per target pair. Same target observations in nested arms.
    target_quota={p:min(20,len(bysys[p])) for p in target_pairs}
    max_target=sum(target_quota.values())
    assert len(binary)>2*max_target
    rng.shuffle(binary)
    # A common core retains every background binary system (and all its molecules).
    representative={}
    for s in binary: representative.setdefault(system(s),s)
    reps=set(map(sample_id,representative.values()))
    remaining=[s for s in binary if sample_id(s) not in reps]
    reserve=remaining[:max_target]
    core=[s for s in binary if sample_id(s) not in set(map(sample_id,reserve))]
    audit=[]
    (OUT/'splits').mkdir(exist_ok=True)
    all_test_ids=sorted(map(sample_id,test)); all_val_ids=sorted(map(sample_id,validation))
    orders=list(permutations(range(3)))
    random.Random(41000).shuffle(orders)
    for seed in range(5):
        rr=random.Random(41000+seed)
        permutation=orders[seed]
        rank={p:permutation.index(c)+1 for p,c in colors.items()}
        picked={}
        for p in sorted(target_pairs):
            candidates=sorted(bysys[p],key=sample_id);rr.shuffle(candidates)
            picked[p]=candidates[:target_quota[p]]
        replacements=list(reserve);rr.shuffle(replacements)
        for k in range(4):
            selected=[s for p in sorted(picked) if rank[p]<=k for s in picked[p]]
            train=core+fixed+selected+replacements[:max_target-len(selected)]
            observed=set().union(*(pairs(s) for s in train))
            assert all(len(set(combinations(t,2))&observed)==k for t in eligible)
            assert len(train)==len(bg)
            assert not {system(s) for s in train}&{system(s) for s in test+validation}
            ids=sorted(map(sample_id,train))
            assert len(ids)==len(set(ids))
            payload={'seed':seed,'coverage':k,'dataset_sha256':dataset_digest(samples),
                'partitions':{'train':ids,'validation':all_val_ids,'test':all_test_ids},
                'target_pair_rank':[{'pair':p,'rank':rank[p],'quota':target_quota[p]} for p in sorted(rank)]}
            (OUT/'splits'/f'coverage_{k}_seed_{seed}.json').write_text(json.dumps(payload,indent=2),encoding='utf-8')
            audit.append({'seed':seed,'coverage':k,'train_rows':len(train),'binary_rows':sum(len(s.smiles)==2 for s in train),'ternary_rows':sum(len(s.smiles)==3 for s in train),'target_binary_rows':len(selected),'validation_rows':len(validation),'test_rows':len(test),'test_systems':len(eligible),'all_systems_exact_coverage':True})
    summary={'design':'Exploratory paired intervention on binary-pair coverage with a fixed ternary test set.',
        'dataset_sha256':dataset_digest(samples),'eligible_target_systems':eligible,'test_rows':len(test),
        'initial_candidates':initial_candidates,'excluded_for_molecular_exposure_confound':excluded,
        'test_mode_counts':dict(Counter(str(s.experiment_mode) for s in test)),
        'background_training_rows':len(bg),'validation_rows':len(validation),'target_pairs':len(target_pairs),
        'maximum_target_rows':max_target,'pair_quota_cap':20,'seeds':list(range(5)),
        'target_pair_exclusion':'All target pairs excluded from common training background and fixed validation, including pairs embedded in other ternaries.',
        'sampling':'Fixed background core, rotating color classes across seeds, nested target-pair additions, binary background rows replaced one-for-one. No replacement sampling.',
        'limitations':['Target systems must have all 3 binary pairs available after standard pure-anchor filtering.',
            'Equal total and binary/ternary training counts; state distributions are not exactly matched.',
            'Five seeds vary initialization, pair order and target-point subsampling; results describe this intervention, not a universal law.',
            'Validation contains no target pairs, so target-chemistry validation adaptation is excluded.']}
    (OUT/'design.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    with (OUT/'split_audit.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(audit[0]));w.writeheader();w.writerows(audit)
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    OUT=args.output_dir.resolve()
    OUT.mkdir(parents=True,exist_ok=True)
    main()
