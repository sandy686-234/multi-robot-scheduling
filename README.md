# Multi-Robot Scheduling and VeriROS Artifacts

This repository contains the code and artifacts for SMT-based heterogeneous
multi-robot scheduling and the VeriROS verified-execution tool.

## Repository Layout

```text
multi-robot-scheduling/
├── synasc2026/
│   ├── scheduler.py
│   ├── validator.py
│   ├── diagnosis.py
│   ├── experiments/
│   └── README.md
├── veriros/
│   ├── ros2_nodes/
│   ├── schedule_follower/
│   ├── resource_manager/
│   ├── safety_fence/
│   ├── stl_monitor/
│   ├── audit/
│   └── README.md
├── artifacts/
│   ├── schedules/
│   ├── traces/
│   ├── logs/
│   └── figures/
└── README.md
```

## Quick Start

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m synasc2026.experiments.run_veriros_paper_experiment --quick
```

Run the full paper-aligned experiment:

```bash
python -m synasc2026.experiments.run_veriros_paper_experiment
```

The full experiment evaluates 3r6t, 6r12t, 7r14t, and 8r16t warehouse-style
instances. The generated summaries are written to
`synasc2026/experiments/results/`.

## Main Results

The paper-aligned experiment uses the same scenario generator and seed policy
for Greedy and VeriROS-SMT runs.

| Config | Greedy Avg Makespan | VeriROS-SMT Avg Makespan | SMT Time |
|---|---:|---:|---:|
| 3r6t | 99.19 s | 72.14 s | 0.0276 s |
| 6r12t | 135.94 s | 96.34 s | 0.5815 s |
| 7r14t | 165.60 s | 103.22 s | 1.8151 s |
| 8r16t | 177.84 s | 109.81 s | 3.3496 s |

## Artifact Evidence

Representative generated evidence is available under `artifacts/`:

- `artifacts/schedules/`: representative `schedule.json` files.
- `artifacts/traces/`: per-robot traces and mutex traces.
- `artifacts/logs/`: Z3 result summaries and violation logs.
- `artifacts/figures/`: paper figures and architecture diagrams.

## License

This repository is a research artifact. Add the final license file before public
artifact review if a specific license is required by the venue.

