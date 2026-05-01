# SMT-Based Multi-Robot Scheduling

Z3 SMT solver for heterogeneous multi-robot task scheduling with temporal, 
capability, and resource constraints.

## Quick Start

```bash
pip install z3-solver
python step4_modified_smt_solver.py
```

## Features

✅ Task assignment to capable robots  
✅ Temporal constraint verification  
✅ Resource mutex handling  
✅ Makespan optimization  

## Usage

```python
from step4_modified_smt_solver import HeterogeneousScheduler

config = {
    "global_deadline": 100.0,
    "robots": [...],
    "tasks": [...],
    "resources": {}
}

scheduler = HeterogeneousScheduler(config)
result = scheduler.solve()

if result:
    print(f"Makespan: {result['makespan']:.2f}s")
```

## Part of VeriROS

Formal verification component for autonomous robot scheduling.  
📄 *FormaliSE 2026*

**Contact:** huan.zhang@mumail.ie
