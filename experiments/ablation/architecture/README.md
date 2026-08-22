# Formal architecture ablations

A0 is the current Full hybrid model. The A1 family isolates molecular information:
Uni-Mol v2 only, RDKit descriptors only, and each one-branch removal from the
three-branch fusion. A2--A6 each alter one controlled downstream modeling choice;
A7 is omitted because no additional scientifically distinct solver removal exists
beyond A6 direct VLE prediction. All runnable commands are recorded in each
variant's `run.md` and share `scripts/run_ablation_suite.py`.

The historical Uni-Mol-only results are an immutable comparator, not the new Full
model. New hybrid-dependent variants are retrained with the same fixed splits,
training budget, validation-only selection, and seeds 0--4. Every molecular
representation variant is evaluated on all three core benchmarks so the comparison
covers ordinary held-out systems, unseen components, and binary-to-ternary transfer.
