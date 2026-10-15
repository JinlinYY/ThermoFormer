# Installation

The GPU/reference environment is declared in [`environment.yml`](../../environment.yml). A CPU-oriented environment is declared in [`environment-cpu.yml`](../../environment-cpu.yml).

```bash
conda env create -f environment.yml
conda activate ggnn39
python -m pip install -e .
```

The project depends on PyTorch, RDKit, phasepy, thermo, and the pinned baseline packages in [`requirements.txt`](../../requirements.txt). Install the PyTorch build appropriate for the host before running model experiments.
