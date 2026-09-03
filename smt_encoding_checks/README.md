# SMT Encoding Checks

This directory contains minimal SMT-LIB checks for the constraint families used
by the VeriROS scheduler. Each file is intentionally small so the expected
semantics can be inspected by hand and checked directly with Z3.

Run all checks:

```bash
python3 tools/run_smt_encoding_checks.py
```

Or run one file directly:

```bash
z3 smt_encoding_checks/precedence_sat.smt2
```

Expected outcomes:

| File | Expected | Constraint family |
|---|---:|---|
| `time_sat.smt2` | `sat` | task start/end/deadline timing |
| `time_unsat.smt2` | `unsat` | impossible duration/deadline timing |
| `assignment_sat.smt2` | `sat` | exactly-one task assignment |
| `assignment_unsat.smt2` | `unsat` | conflicting assignment decisions |
| `capability_sat.smt2` | `sat` | incapable robot forced false |
| `capability_unsat.smt2` | `unsat` | incapable robot forced true |
| `travel_ordering_sat.smt2` | `sat` | same-robot task ordering with travel |
| `travel_ordering_unsat.smt2` | `unsat` | overlap despite travel requirement |
| `precedence_sat.smt2` | `sat` | predecessor finishes before successor starts |
| `precedence_unsat.smt2` | `unsat` | successor starts before predecessor finishes |
| `resource_mutex_sat.smt2` | `sat` | non-overlapping shared resource intervals |
| `resource_mutex_unsat.smt2` | `unsat` | overlapping shared resource intervals |
| `full_schedule_sat.smt2` | `sat` | integrated schedule constraints |
| `full_schedule_unsat.smt2` | `unsat` | integrated precedence violation |

