#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STEP 3: Modified Greedy Scheduler

Uses unified time calculation library for consistency.
"""

import math
import time
import random
from typing import Dict, List, Tuple, Optional, Any

from step2_unified_time_library import (
    TravelTimeCalculator,
    ResourceOverheadCalculator,
    TimeComparison,
    TimeConstraintValidator,
)


def build_task_pool(cfg: Dict) -> Dict:
    task_pool = {}
    for t in cfg.get("tasks", []):
        tid = t.get("id")
        if not tid:
            continue
        
        duration = float(t.get("duration", 0.0))
        deadline = float(t.get("deadline", 1e9))
        
        if duration < 0 or deadline < 0:
            raise ValueError(f"Task {tid}: invalid duration or deadline")
        
        task_pool[tid] = {
            "id": tid,
            "location": tuple(t.get("location", [0.0, 0.0])),
            "duration": duration,
            "deadline": deadline,
            "requires_capability": t.get("requires_capability", None),
            "uses_resources": list(t.get("uses_resources", [])),
        }
    
    return task_pool


def build_robots(cfg: Dict) -> Dict:
    robots = {}
    for r in cfg.get("robots", []):
        rid = r.get("id") or r.get("name")
        if not rid:
            continue
        
        max_speed = float(r.get("max_speed", 1.0))
        if max_speed < 0:
            raise ValueError(f"Robot {rid}: invalid max_speed")
        
        robots[rid] = {
            "id": rid,
            "name": r.get("name", rid),
            "capabilities": list(r.get("capabilities", [])),
            "max_speed": max_speed,
            "start_position": tuple(r.get("start_position", [0.0, 0.0])),
        }
    
    return robots


def build_resources(cfg: Dict) -> Dict:
    resources = {}
    for res_name, res_spec in cfg.get("resources", {}).items():
        traversal_time = float(res_spec.get("traversal_time", 0.0))
        if traversal_time < 0:
            raise ValueError(f"Resource {res_name}: invalid traversal_time")
        
        resources[res_name] = {
            "name": res_name,
            "traversal_time": traversal_time,
            "type": res_spec.get("type", "mutex"),
        }
    
    return resources


class GreedyScheduler:
    """Greedy scheduler with unified time calculation."""

    def __init__(self, cfg: Dict, seed: Optional[int] = None):
        self.cfg = cfg
        self.task_pool = build_task_pool(cfg)
        self.robots = build_robots(cfg)
        self.resources = build_resources(cfg)
        self.global_deadline = float(cfg.get("global_deadline", 1e9))
        self.failure_reason = None
        if seed is not None:
            random.seed(seed)

    def _capable(self, rid: str, tid: str) -> bool:
        req = self.task_pool[tid].get("requires_capability")
        if req is None:
            return True
        return req in self.robots[rid].get("capabilities", [])

    def solve(self) -> Optional[Dict]:
        t0 = time.time()

        task_ids = list(self.task_pool.keys())
        robot_ids = list(self.robots.keys())

        if not task_ids or not robot_ids:
            self.failure_reason = "empty_instance"
            return None

        # Initialize robot state
        robot_state = {}
        for rid in robot_ids:
            robot_state[rid] = {
                "time": 0.0,
                "pos": tuple(self.robots[rid]["start_position"]),
                "tasks": [],
            }

        # Initialize resource state
        resource_free_at = {r: 0.0 for r in self.resources.keys()}

        # Sort tasks by deadline
        task_ids.sort(key=lambda tid: self.task_pool[tid]["deadline"])

        # Main scheduling loop
        for tid in task_ids:
            task = self.task_pool[tid]
            candidates = []

            for rid in robot_ids:
                if not self._capable(rid, tid):
                    continue

                rstate = robot_state[rid]
                max_speed = self.robots[rid]["max_speed"]

                travel_time = TravelTimeCalculator.compute(
                    rstate["pos"],
                    task["location"],
                    max_speed
                )

                est = rstate["time"] + travel_time
                eet = est + task["duration"]

                # Check resource constraints
                for res in task.get("uses_resources", []):
                    if res in resource_free_at:
                        res_free_time = resource_free_at[res]
                        if est < res_free_time - TimeComparison.EPS:
                            est = res_free_time
                    eet = est + task["duration"]

                candidates.append((eet, est, rid))

            if not candidates:
                self.failure_reason = "capability_mismatch"
                return None

            # Select candidate with minimum end time
            candidates.sort(key=lambda x: x[0])
            num_cand = min(3, len(candidates))
            best_end, best_start, best_rid = random.choice(candidates[:num_cand])

            # Check deadline constraints
            task_deadline = task["deadline"]
            task_complies, _ = TimeConstraintValidator.check_deadline_compliance(
                best_end, task_deadline
            )
            if not task_complies:
                self.failure_reason = "task_deadline_conflict"
                return None

            global_complies, _ = TimeConstraintValidator.check_global_deadline_compliance(
                best_end, self.global_deadline
            )
            if not global_complies:
                self.failure_reason = "global_deadline_conflict"
                return None

            # Assign task
            robot_state[best_rid]["tasks"].append({
                "task_id": tid,
                "start_time": float(best_start),
                "end_time": float(best_end),
                "duration": float(task["duration"]),
                "location": list(task["location"]),
            })
            robot_state[best_rid]["time"] = best_end
            robot_state[best_rid]["pos"] = tuple(task["location"])

            # Update resource state
            for res in task.get("uses_resources", []):
                if res in self.resources:
                    resource_oh = ResourceOverheadCalculator.compute(
                        self.resources[res]["traversal_time"]
                    )
                    resource_free_at[res] = best_end + resource_oh

        # Build schedule result
        schedules = {rid: robot_state[rid]["tasks"] for rid in robot_ids}

        # Build resource allocation info
        resource_allocation = {}
        for res in self.resources.keys():
            resource_allocation[res] = []
            for rid in robot_ids:
                for task_entry in schedules[rid]:
                    tid = task_entry["task_id"]
                    if res in self.task_pool[tid].get("uses_resources", []):
                        resource_oh = ResourceOverheadCalculator.compute(
                            self.resources[res]["traversal_time"]
                        )
                        resource_allocation[res].append({
                            "robot": rid,
                            "task_id": tid,
                            "start_time": task_entry["start_time"],
                            "end_time": task_entry["end_time"],
                            "resource_hold_duration": (
                                task_entry["end_time"] - task_entry["start_time"] + resource_oh
                            ),
                        })
            resource_allocation[res].sort(key=lambda x: x["start_time"])

        # Compute makespan
        makespan = 0.0
        for rid in robot_ids:
            if schedules[rid]:
                completion = schedules[rid][-1]["end_time"]
                makespan = max(makespan, completion)

        # Validate schedule
        for res_name, allocations in resource_allocation.items():
            mutex_ok = TimeConstraintValidator.check_resource_mutex(allocations)
            if not mutex_ok:
                self.failure_reason = f"resource_mutex_violated: {res_name}"
                return None

        return {
            "feasible": True,
            "optimal": False,
            "status": "greedy",
            "solver_time": time.time() - t0,
            "makespan": makespan,
            "schedules": schedules,
            "resource_allocation": resource_allocation,
            "global_deadline": self.global_deadline,
            "num_robots": len(robot_ids),
            "num_tasks": len(task_ids),
            "time_calculation_method": "TravelTimeCalculator (unified)",
            "time_units": "seconds",
            "spatial_units": "meters",
            "speed_units": "m/s",
        }


if __name__ == "__main__":
    print("=" * 70)
    print("GREEDY SCHEDULER - TEST")
    print("=" * 70)

    config = {
        "global_deadline": 150,
        "robots": [
            {
                "id": "A",
                "name": "Forklift",
                "capabilities": ["heavy_lift"],
                "max_speed": 0.5,
                "start_position": [0.0, 0.0]
            }
        ],
        "tasks": [
            {
                "id": "task1",
                "location": [5.0, 0.0],
                "duration": 10,
                "deadline": 60,
                "requires_capability": "heavy_lift",
                "uses_resources": []
            }
        ],
        "resources": {}
    }

    scheduler = GreedyScheduler(config)
    result = scheduler.solve()

    if result:
        print(f"\nScheduling succeeded!")
        print(f"  Feasible: {result['feasible']}")
        print(f"  Makespan: {result['makespan']:.2f} {result['time_units']}")
        print(f"  Solver time: {result['solver_time']*1000:.2f} ms")
        print(f"  Time calculation: {result['time_calculation_method']}")
        
        print(f"\nSchedule details:")
        for robot_id, tasks in result["schedules"].items():
            print(f"  Robot {robot_id}: {len(tasks)} tasks")
            for task in tasks:
                print(f"    - {task['task_id']}: [{task['start_time']:.2f}, {task['end_time']:.2f}]")
    else:
        print(f"\nScheduling failed!")
        print(f"  Reason: {scheduler.failure_reason}")

    print("\n" + "=" * 70)
