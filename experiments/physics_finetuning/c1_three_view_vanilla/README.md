# C1 partial physics fine-tuning

This experiment reuses the committed C1 supervised seed-0 checkpoint, freezes
the molecular views and vanilla Transformer, and fine-tunes only the declared
thermodynamic modules for five epochs. Selection remains validation-only.

Only `overall_binary_ternary`, seed 0 is registered for this experiment.
