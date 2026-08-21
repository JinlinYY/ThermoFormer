# Formal checkpoints

Best ThermoFormer checkpoints are stored as
`checkpoints/<protocol>/seed_<n>/best_model.pt` and versioned with Git LFS.
Each file has a matching formal run manifest under
`results/<protocol>/seed_<n>/manifest.json`; the manifest records its SHA256,
training Git commit, split file, dataset digest, feature digest, environment and
resolved configuration.

After cloning the repository, install Git LFS and materialize the weights with:

```bash
git lfs install
git lfs pull
```
