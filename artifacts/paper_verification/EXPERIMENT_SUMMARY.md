# VeriROS Experiment Summary

This artifact evaluates VeriROS on reproducible warehouse scheduling scenarios 
with heterogeneous robots, shared mutex resources, precedence constraints, and deadlines.

## Experimental Design

- Scenario generator: `generate_warehouse_config` in `paper_artifacts.py`.
- Baseline: randomized greedy scheduler.
- VeriROS: SMT scheduler backed by Z3 when `z3-solver` is installed.
- Shared resources: `corridor_A`, `loading_zone`, `charging_station`.
- Precedence pattern: `task_{4k+1}` must finish before `task_{4k+3}` can start.
- Representative evidence files are written under `<output-dir>/<config>/seed_<seed>/`.

## Results

| Config | Solver | Feasible | Avg makespan (s) | Avg solve time (s) | Status note |
|---|---:|---:|---:|---:|---|
| 3r6t | Greedy | 10/10 | 99.19 | 0.0001 | ok |
| 3r6t | VeriROS-SMT | 3/3 | 72.14 | 0.0421 | ok |
| 6r12t | Greedy | 10/10 | 135.94 | 0.0001 | ok |
| 6r12t | VeriROS-SMT | 3/3 | 98.97 | 1.0780 | ok |
| 7r14t | Greedy | 10/10 | 165.60 | 0.0001 | ok |
| 7r14t | VeriROS-SMT | 3/3 | 105.65 | 2.7954 | ok |
| 8r16t | Greedy | 10/10 | 177.84 | 0.0002 | ok |
| 8r16t | VeriROS-SMT | 3/3 | 109.98 | 4.8746 | ok |

## Paper Alignment Notes

- The Greedy and VeriROS-SMT runs now use the same scenario generator and seed policy.
- The generated schedules include resource-allocation traces for checking mutex conflicts.
- The generated schedules include precedence edges checked by the independent validator.
- If `z3-solver` is missing, SMT rows are marked as skipped instead of being mixed with Greedy-only data.
