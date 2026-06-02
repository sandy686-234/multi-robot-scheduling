# Scheduling Experiment Summary

## Scope

The experiment keeps the original Greedy and SMT/Z3 schedulers. It does not change the solver logic to QF_LIRA and does not restructure the scheduler into separate planner/verifier modules.

Tested configurations:

- 3 robots / 6 tasks
- 6 robots / 12 tasks
- 7 robots / 14 tasks
- 8 robots / 16 tasks

## Greedy vs SMT results

Settings:

- Greedy: 10 runs per configuration
- SMT/Z3: 3 runs per configuration
- SMT timeout: 60 seconds per run
- Base seed: 100

| Config | Greedy feasible | Greedy avg makespan | SMT feasible | SMT avg makespan | SMT avg time |
|---|---:|---:|---:|---:|---:|
| 3r6t | 8/10 | 103.21 s | 3/3 | 62.92 s | 0.088 s |
| 6r12t | 10/10 | 138.74 s | 3/3 | 75.78 s | 3.122 s |
| 7r14t | 10/10 | 138.18 s | 3/3 | 83.53 s | 9.712 s |
| 8r16t | 9/10 | 126.81 s | 3/3 | 76.09 s | 17.189 s |

No SMT timeout occurred in these runs.

## Greedy variability results

Settings:

- 10 seeds per configuration
- Seeds: 100-109

| Config | Feasible runs | Avg makespan | Min makespan | Max makespan |
|---|---:|---:|---:|---:|
| 3x6 | 1/10 | 107.71 s | 107.71 s | 107.71 s |
| 6x12 | 8/10 | 125.89 s | 97.85 s | 169.86 s |
| 7x14 | 7/10 | 105.97 s | 84.94 s | 142.01 s |
| 8x16 | 7/10 | 115.83 s | 92.09 s | 154.23 s |

## Notes

Greedy runs very quickly and scales well, but it may fail on some random instances because it makes local choices. SMT/Z3 gives better makespan values in these tests and solved all sampled instances, but its runtime increases as the number of robots and tasks grows.

Generated result files:

- `comparison_results_large_scale.json`
- `comparison_results_large_scale.csv`
- `greedy_variability_results.json`
