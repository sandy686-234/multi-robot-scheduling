# SYNASC 2026 Scheduling Components

This package contains the SMT scheduling artifact and experiment code.

## Files

- `scheduler.py`: Z3-based heterogeneous multi-robot scheduler.
- `validator.py`: shared time, travel, resource, and constraint validation utilities.
- `diagnosis.py`: resource-mutex and artifact-diagnosis helpers.
- `semantic_definition.md`: shared symbolic/numeric time and resource semantics.
- `experiments/greedy_scheduler.py`: randomized greedy baseline.
- `experiments/paper_artifacts.py`: paper-aligned scenario generator, experiment runner, and evidence writer.
- `experiments/run_veriros_paper_experiment.py`: command-line entry point for the paper experiment.
- `experiments/results/`: CSV, JSON, and Markdown result summaries.

## Run

```bash
python -m synasc2026.experiments.run_veriros_paper_experiment --quick
python -m synasc2026.experiments.run_veriros_paper_experiment
```

The quick run exercises the 3r6t configuration. The full run evaluates all
paper configurations and regenerates summaries.
