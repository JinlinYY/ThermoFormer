# Agent evaluation commands

The commands implement manuscript Section 2.2 and SI S8:

- `reliability_tasks.py`: task variants and scoring labels.
- `reliability_run.py`: task compilation, numerical execution/cache, and reporting.
- `audit_reliability.py --input <directory>`: read-only record/checkpoint validation.
- `main_figure_experiment.py`: paired gate replay, clarification recovery, and evidence decisions.
- `reliability_report.py` and `main_figure_report.py`: numerical report generation.
- `agent_publication_figure.py`: the final six-panel Fig. 3 and its source tables.

See the [S8 guide](../../../experiments/supporting_information/s8_agent_reliability/README.md)
for installation and complete commands. API keys belong in environment variables.
