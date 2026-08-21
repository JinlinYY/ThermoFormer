# Formal experiment configuration index

The canonical editable experiment configurations remain co-located with their
commands and human-readable results under `experiments/<category>/.../config.json`,
as required by the project layout. The single registry is
`src/paper_protocols.py`.

Every completed seed also contains the exact resolved configuration snapshot at
`results/<protocol>/seed_<seed>/resolved_config.json`. Formal aggregation verifies
the snapshots and their SHA-256 digests before producing protocol summaries.
This directory is therefore an index to the canonical definitions and immutable
run snapshots, not a second set of duplicated configuration files.
