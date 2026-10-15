"""Configure the isolated numerical worker before importing SciPy/PyTorch."""

from __future__ import annotations

import os


def configure_runtime() -> None:
    # ggnn39 contains both Intel and LLVM OpenMP runtimes. Sequential MKL
    # avoids loading a competing runtime; do not enable KMP_DUPLICATE_LIB_OK.
    os.environ["MKL_THREADING_LAYER"] = "SEQUENTIAL"
    os.environ["OMP_NUM_THREADS"] = "1"
