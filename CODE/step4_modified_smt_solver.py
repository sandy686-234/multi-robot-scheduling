#!/usr/bin/env python3
# -*- coding: utf-8 -*-

try:
    from z3 import *
    HAS_Z3 = True
except ImportError:
    HAS_Z3 = False
    print("[Warning] Z3 not installed. SMT solver disabled.")

import time
from typing import Dict, List, Tuple, Optional, Any
import math


from step2_unified_time_library import (
    TravelTimeCalculator,
    ResourceOverheadCalculator,
    TimeComparison,
)


def build_task_pool(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Build task pool."""
    task_pool = {}
    for t in cfg.get("tasks", []):
        tid = t.get("id")
        if not tid:
            continue
        task_pool[tid] = {
            "id": tid,
            "location": tuple(t.get("location", [0.0, 0.0])),
            "duration": float(t.get("duration", 0.0)),
            "deadline": float(t.get("deadline", 1e9)),
            "requires_capability": t.get("requires_capability", None),
            "uses_resources": list(t.get("uses_resources", [])),
        }
    return task_pool


def build_robots(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Build robot pool."""
    robots = {}
    for r in cfg.get("robots", []):
        rid = r.get("id") or r.get("name")
        if not rid:
            continue
        robots[rid] = {
            "id": rid,
            "name": r.get("name", rid),
            "capabilities": list(r.get("capabilities", [])),
            "max_speed": float(r.get("max_speed", 1.0)),
            "start_position": tuple(r.get("start_position", [0.0, 0.0])),
        }
    return robots


def build_resources(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Build resource pool."""
    resources = {}
    for res_name, res_spec in cfg.get("resources", {}).items():
        resources[res_name] = {
            "name": res_name,
            "traversal_time": float(res_spec.get("traversal_time", 0.0)),
            "type": res_spec.get("type", "mutex"),
        }
    return resources


class HeterogeneousScheduler:

    def __init__(self, cfg: Dict[str, Any], time_limit: int = 300000):  # 300s
        if not HAS_Z3:
            raise ImportError("Z3 is required for SMT solver")

        self.cfg = cfg
        self.time_limit = time_limit  # milliseconds

        self.tasks = build_task_pool(cfg)
        self.robots = build_robots(cfg)
        self.resources = build_resources(cfg)
        self.global_deadline = float(cfg.get("global_deadline", 1e9))

        self.solver = None
        self.vars = {}
        self.failure_reason = None

        self.travel_time_constraints = {}  # {(robot, task_i, task_j): time}
        self.resource_overhead_values = {}  # {resource: overhead}

    def capable(self, robot: Dict, task: Dict) -> bool:
     
        req_cap = task.get("requires_capability")
        if req_cap is None:
            return True
        return req_cap in robot.get("capabilities", [])

    def travel_time_from_start(self, robot: Dict, task: Dict) -> float:
      
        TravelTimeCalculator.euclidean_distance(
            robot["start_position"],
            task["location"]
        )
        return TravelTimeCalculator.compute(
            robot["start_position"],
            task["location"],
            robot["max_speed"]
        )

    def travel_time_between_tasks(self, robot: Dict, task_i: Dict, task_j: Dict) -> float:
       
        return TravelTimeCalculator.compute(
            task_i["location"],
            task_j["location"],
            robot["max_speed"]
        )

    def build_smt_model(self) -> bool:
     
        if not HAS_Z3:
            print("[✗] Z3 not installed")
            return False

        self.solver = Optimize()
        self.solver.set("timeout", self.time_limit)

        self.vars = {
            "assign": {},
            "start": {},
            "end": {},
            "order": {},
            "res_start": {},
            "res_end": {},
            "makespan": Real("makespan"),
        }

        robot_ids = list(self.robots.keys())
        task_ids = list(self.tasks.keys())

       
        for task_id in task_ids:
            task = self.tasks[task_id]
            st = Real(f"st_{task_id}")
            et = Real(f"et_{task_id}")
            self.vars["start"][task_id] = st
            self.vars["end"][task_id] = et

            self.solver.add(st >= 0)
            self.solver.add(et == st + task["duration"])
            self.solver.add(et <= task["deadline"])
            self.solver.add(et <= self.global_deadline)

       
        for task_id in task_ids:
            task = self.tasks[task_id]
            candidates = []

            for robot_id in robot_ids:
                robot = self.robots[robot_id]
                a = Bool(f"assign_{robot_id}_{task_id}")
                self.vars["assign"][(robot_id, task_id)] = a

                if not self.capable(robot, task):
                    self.solver.add(a == False)
                else:
                    candidates.append(a)

                    first_travel = self.travel_time_from_start(robot, task)
                    self.solver.add(
                        Implies(a, self.vars["start"][task_id] >= first_travel)
                    )

            if not candidates:
                self.failure_reason = f"capability_mismatch: {task_id}"
                return False

            self.solver.add(Sum([If(v, 1, 0) for v in candidates]) == 1)

        for robot_id in robot_ids:
            robot = self.robots[robot_id]
            task_ids_list = list(self.tasks.keys())

            for i, ti in enumerate(task_ids_list):
                for j, tj in enumerate(task_ids_list):
                    if ti == tj:
                        continue

                    ai = self.vars["assign"][(robot_id, ti)]
                    aj = self.vars["assign"][(robot_id, tj)]

                    ord_ij = Bool(f"ord_{robot_id}_{ti}_{tj}")
                    self.vars["order"][(robot_id, ti, tj)] = ord_ij

                    tt_ij = self.travel_time_between_tasks(
                        robot,
                        self.tasks[ti],
                        self.tasks[tj]
                    )
                    tt_ji = self.travel_time_between_tasks(
                        robot,
                        self.tasks[tj],
                        self.tasks[ti]
                    )

                    self.travel_time_constraints[(robot_id, ti, tj)] = tt_ij
                    self.travel_time_constraints[(robot_id, tj, ti)] = tt_ji

                    self.solver.add(
                        Implies(
                            And(ai, aj),
                            Or(
                                And(ord_ij,
                                    self.vars["start"][tj] >=
                                    self.vars["end"][ti] + tt_ij),
                                And(Not(ord_ij),
                                    self.vars["start"][ti] >=
                                    self.vars["end"][tj] + tt_ji),
                            )
                        )
                    )

        for res_name in self.resources.keys():
            resource = self.resources[res_name]

            resource_oh = ResourceOverheadCalculator.compute(
                resource["traversal_time"]
            )
            self.resource_overhead_values[res_name] = resource_oh

            tasks_using_res = [
                t_id for t_id, task in self.tasks.items()
                if res_name in task.get("uses_resources", [])
            ]

            for task_id in tasks_using_res:
                res_st = Real(f"res_st_{res_name}_{task_id}")
                res_et = Real(f"res_et_{res_name}_{task_id}")

                self.vars["res_start"][(res_name, task_id)] = res_st
                self.vars["res_end"][(res_name, task_id)] = res_et

                self.solver.add(res_st == self.vars["start"][task_id])
                self.solver.add(
                    res_et == self.vars["end"][task_id] + resource_oh
                )

            for i in range(len(tasks_using_res)):
                for j in range(i + 1, len(tasks_using_res)):
                    ti = tasks_using_res[i]
                    tj = tasks_using_res[j]

                    b = Bool(f"res_before_{res_name}_{ti}_{tj}")

                    self.solver.add(
                        Or(
                            And(b,
                                self.vars["res_end"][(res_name, ti)] <=
                                self.vars["res_start"][(res_name, tj)]),
                            And(Not(b),
                                self.vars["res_end"][(res_name, tj)] <=
                                self.vars["res_start"][(res_name, ti)]),
                        )
                    )

        makespan = self.vars["makespan"]
        self.solver.add(makespan >= 0)
        for task_id in task_ids:
            self.solver.add(makespan >= self.vars["end"][task_id])

        self.solver.minimize(makespan)
        return True

    def _z3_value_to_float(self, value: Any) -> float:
     
        if hasattr(value, "numerator_as_long") and hasattr(value, "denominator_as_long"):
            numerator = value.numerator_as_long()
            denominator = value.denominator_as_long()
            return numerator / denominator
        if hasattr(value, "as_decimal"):
            dec = value.as_decimal(20)
            if isinstance(dec, str) and dec.endswith("?"):
                dec = dec[:-1]
            return float(dec)
        return float(value)

    def solve(self) -> Optional[Dict[str, Any]]:
       
        if not self.build_smt_model():
            return None

        result = self.solver.check()
        if result != sat:
            self.failure_reason = f"Z3_returned: {result}"
            return None

        m = self.solver.model()

        schedules = {}
        for robot_id in self.robots.keys():
            schedules[robot_id] = []

        for task_id in self.tasks.keys():
            for robot_id in self.robots.keys():
                assign_var = self.vars["assign"][(robot_id, task_id)]
                if is_true(m.eval(assign_var)):
                    start_val = self._z3_value_to_float(m.eval(self.vars["start"][task_id]))
                    end_val = self._z3_value_to_float(m.eval(self.vars["end"][task_id]))

                    schedules[robot_id].append({
                        "task_id": task_id,
                        "start_time": start_val,
                        "end_time": end_val,
                        "duration": self.tasks[task_id]["duration"],
                        "location": list(self.tasks[task_id]["location"]),
                    })

        resource_allocation = {}
        for res_name in self.resources.keys():
            resource_allocation[res_name] = []
            for robot_id in self.robots.keys():
                for task_entry in schedules[robot_id]:
                    task_id = task_entry["task_id"]
                    if res_name in self.tasks[task_id].get("uses_resources", []):
                        resource_overhead = self.resource_overhead_values[res_name]
                        resource_allocation[res_name].append({
                            "robot": robot_id,
                            "task_id": task_id,
                            "start_time": task_entry["start_time"],
                            "end_time": task_entry["end_time"] + resource_overhead,
                        })
            resource_allocation[res_name].sort(key=lambda x: x["start_time"])

        makespan = self._z3_value_to_float(m.eval(self.vars["makespan"]))

        return {
            "feasible": True,
            "optimal": True,
            "status": "sat",
            "solver_time": 0.0,  # Z3 internal timing
            "makespan": makespan,
            "schedules": schedules,
            "resource_allocation": resource_allocation,
            "global_deadline": self.global_deadline,
            "num_robots": len(self.robots),
            "num_tasks": len(self.tasks),
            "time_calculation_method": "TravelTimeCalculator (unified)",
            "time_units": "seconds",
            "spatial_units": "meters",
            "speed_units": "m/s",
            "travel_time_constraints": self.travel_time_constraints,
            "resource_overhead_values": self.resource_overhead_values,
        }



def generate_random_config(num_robots: int, num_tasks: int, seed: int) -> Dict[str, Any]:
    """Generate a random scheduling config with a fixed seed for reproducibility."""
    import random
    rng = random.Random(seed)

    capabilities = ["basic", "heavy", "precision"]
    area_size = 20.0 + num_tasks * 2.0
    global_deadline = 60.0 + num_tasks * 15.0 + num_robots * 5.0

    robots = []
    for i in range(num_robots):
        cap_subset = rng.sample(capabilities, k=rng.randint(1, len(capabilities)))
        speed = round(rng.uniform(0.4, 1.2), 2)
        robots.append({
            "id": f"R{i+1}",
            "name": f"Robot{i+1}",
            "capabilities": cap_subset,
            "max_speed": speed,
            "start_position": [
                round(rng.uniform(0, area_size), 1),
                round(rng.uniform(0, area_size), 1),
            ],
        })

    tasks = []
    for j in range(num_tasks):
        cap = rng.choice(capabilities)
        duration = round(rng.uniform(3.0, 12.0), 1)
        slack = round(rng.uniform(20.0, 50.0), 1)
        tasks.append({
            "id": f"T{j+1}",
            "location": [
                round(rng.uniform(0, area_size), 1),
                round(rng.uniform(0, area_size), 1),
            ],
            "duration": duration,
            "deadline": global_deadline,
            "requires_capability": cap,
            "uses_resources": [],
        })

    return {
        "global_deadline": global_deadline,
        "robots": robots,
        "tasks": tasks,
        "resources": {},
    }


def run_scalability_benchmark(
    configs: List[Tuple[int, int]],
    runs_per_config: int = 10,
    base_seed: int = 42,
    time_limit_ms: int = 30000,
) -> None:

    import statistics

    print("=" * 70)
    print("SMT SOLVER SCALABILITY BENCHMARK")
    print(f"  configs: {configs}")
    print(f"  runs per config: {runs_per_config}  (seeds {base_seed} … {base_seed + runs_per_config - 1})")
    print(f"  solver timeout: {time_limit_ms // 1000}s per run")
    print("=" * 70)

    header = f"{'Config':>12} | {'Feasible':>10} | {'Mean(s)':>9} | {'Std(s)':>8} | {'Min(s)':>8} | {'Max(s)':>8} | {'Wall(s)':>8}"
    print(header)
    print("-" * len(header))

    for (nr, nt) in configs:
        label = f"{nr}r{nt}t"
        makespans = []
        wall_times = []
        feasible_count = 0

        for run_idx in range(runs_per_config):
            seed = base_seed + run_idx          # different seed every run → different layout
            cfg = generate_random_config(nr, nt, seed)

            t0 = time.time()
            try:
                scheduler = HeterogeneousScheduler(cfg, time_limit=time_limit_ms)
                result = scheduler.solve()
            except Exception:
                result = None
            wall = time.time() - t0
            wall_times.append(wall)

            if result and result.get("feasible"):
                feasible_count += 1
                makespans.append(result["makespan"])

        feasible_pct = feasible_count / runs_per_config * 100

        if len(makespans) >= 2:
            mean_ms = statistics.mean(makespans)
            std_ms  = statistics.stdev(makespans)
            min_ms  = min(makespans)
            max_ms  = max(makespans)
        elif len(makespans) == 1:
            mean_ms = makespans[0]
            std_ms  = 0.0
            min_ms  = max_ms = makespans[0]
        else:
            mean_ms = std_ms = min_ms = max_ms = float("nan")

        mean_wall = statistics.mean(wall_times)

        print(
            f"{label:>12} | {feasible_pct:>9.0f}% | "
            f"{mean_ms:>9.2f} | {std_ms:>8.2f} | "
            f"{min_ms:>8.2f} | {max_ms:>8.2f} | "
            f"{mean_wall:>8.2f}"
        )

    print("=" * 70)
    print("  Makespan unit: seconds   Wall time: seconds per run")



if __name__ == "__main__":
    # --- quick single-run smoke test ---
    print("=" * 70)
    print("MODIFIED SMT SOLVER - SINGLE-RUN TEST")
    print("=" * 70)

    cfg_single = generate_random_config(num_robots=2, num_tasks=4, seed=0)
    scheduler = HeterogeneousScheduler(cfg_single, time_limit=30000)
    result = scheduler.solve()

    if result:
        print(f"  Feasible : {result['feasible']}")
        print(f"  Makespan : {result['makespan']:.2f} {result['time_units']}")
        print(f"  Method   : {result['time_calculation_method']}")
    else:
        print(f"  FAILED   : {scheduler.failure_reason}")

    print()

    run_scalability_benchmark(
        configs=[
            (2, 4),
            (3, 6),
            (4, 8),
            (5, 10),
        ],
        runs_per_config=10,
        base_seed=100,
        time_limit_ms=30000,
    )
