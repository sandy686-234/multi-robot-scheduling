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
python -m synasc2026.experiments.run_veriros_paper_experiment --output-dir artifacts/paper_verification
```

The full experiment evaluates 3r6t, 6r12t, 7r14t, and 8r16t warehouse-style
instances. The reproduced paper artifacts are written to
`artifacts/paper_verification/`.

## Main Results

The paper-aligned experiment uses the same scenario generator and seed policy
for Greedy and VeriROS-SMT runs. Each generated mission includes heterogeneous
capability requirements, shared mutex resources, deadlines, and precedence
edges of the form `task_{4k+1} -> task_{4k+3}`.

| Config | Greedy Avg Makespan | VeriROS-SMT Avg Makespan | SMT Time |
|---|---:|---:|---:|
| 3r6t | 99.19 s | 72.14 s | 0.0421 s |
| 6r12t | 135.94 s | 98.97 s | 1.0780 s |
| 7r14t | 165.60 s | 105.65 s | 2.7954 s |
| 8r16t | 177.84 s | 109.98 s | 4.8746 s |

## Artifact Evidence

Representative generated evidence is available under `artifacts/paper_verification/`:

- `<config>/seed_100/<solver>/schedule.json`: representative schedules, including precedence edges.
- `<config>/seed_100/<solver>/mutex_trace.csv`: shared-resource allocation traces.
- `<config>/seed_100/<solver>/trace_robot_*.csv`: per-robot execution traces.
- `<config>/seed_100/<solver>/z3_result.txt` and `violations.log`: solver summaries and validation logs.

## License

This repository is a research artifact. Add the final license file before public
artifact review if a specific license is required by the venue.
