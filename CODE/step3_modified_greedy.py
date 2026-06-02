#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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


def build_task_pool(cfg: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Build task pool. All time values in seconds, positions in meters."""
    task_pool: Dict[str, Dict[str, Any]] = {}
    for t in cfg.get("tasks", []):
        tid = t.get("id")
        if not tid:
            continue

        duration = float(t.get("duration", 0.0))  # seconds
        deadline = float(t.get("deadline", 1e9))  # seconds

        if duration < 0:
            raise ValueError(f"Task {tid}: duration cannot be negative: {duration}")
        if deadline < 0:
            raise ValueError(f"Task {tid}: deadline cannot be negative: {deadline}")

        task_pool[tid] = {
            "id": tid,
            "location": tuple(t.get("location", [0.0, 0.0])),  # meters
            "duration": duration,  # seconds
            "deadline": deadline,  # seconds
            "requires_capability": t.get("requires_capability", None),
            "uses_resources": list(t.get("uses_resources", [])),
        }

    return task_pool


def build_robots(cfg: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Build robot pool. max_speed in m/s, start_position in meters."""
    robots: Dict[str, Dict[str, Any]] = {}
    for r in cfg.get("robots", []):
        rid = r.get("id") or r.get("name")
        if not rid:
            continue

        max_speed = float(r.get("max_speed", 1.0))  # m/s

        if max_speed < 0:
            raise ValueError(f"Robot {rid}: max_speed cannot be negative: {max_speed}")

        robots[rid] = {
            "id": rid,
            "name": r.get("name", rid),
            "capabilities": list(r.get("capabilities", [])),
            "max_speed": max_speed,  # m/s
            "start_position": tuple(r.get("start_position", [0.0, 0.0])),  # meters
        }

    return robots


def build_resources(cfg: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Build resource pool. traversal_time is resource overhead in seconds."""
    resources: Dict[str, Dict[str, Any]] = {}
    for res_name, res_spec in cfg.get("resources", {}).items():
        traversal_time = float(res_spec.get("traversal_time", 0.0))  # seconds

        if traversal_time < 0:
            raise ValueError(
                f"Resource {res_name}: traversal_time cannot be negative: {traversal_time}"
            )

        resources[res_name] = {
            "name": res_name,
            "traversal_time": traversal_time,  # seconds (resource overhead, NOT travel time)
            "type": res_spec.get("type", "mutex"),
            "rect": res_spec.get("rect", None),
        }

    return resources


class GreedyScheduler:


    def __init__(self, cfg: Dict[str, Any], seed: Optional[int] = None):
        self.cfg = cfg
        self.task_pool = build_task_pool(cfg)
        self.robots = build_robots(cfg)
        self.resources = build_resources(cfg)
        self.global_deadline = float(cfg.get("global_deadline", 1e9))  # seconds
        self.failure_reason: Optional[str] = None
        if seed is not None:
            random.seed(seed)

    def _capable(self, rid: str, tid: str) -> bool:
      
        req = self.task_pool[tid].get("requires_capability")
        if req is None:
            return True
        return req in self.robots[rid].get("capabilities", [])

    def solve(self) -> Optional[Dict[str, Any]]:
        """Greedy multi-robot scheduling."""
        t0 = time.time()

        task_ids = list(self.task_pool.keys())
        robot_ids = list(self.robots.keys())

        if not task_ids or not robot_ids:
            self.failure_reason = "empty_instance"
            return None

  
        robot_state: Dict[str, Dict[str, Any]] = {}
        for rid in robot_ids:
            robot_state[rid] = {
                "time": 0.0,  # seconds
                "pos": tuple(self.robots[rid]["start_position"]),  # meters
                "tasks": [],
            }

        resource_free_at: Dict[str, float] = {
            r: 0.0 for r in self.resources.keys()
        }  # seconds

   
        task_ids.sort(key=lambda tid: self.task_pool[tid]["deadline"])

      
        for tid in task_ids:
            task = self.task_pool[tid]

            candidates = []
            for rid in robot_ids:
                if not self._capable(rid, tid):
                    continue

                rstate = robot_state[rid]
                max_speed = self.robots[rid]["max_speed"]  # m/s

                travel_time = TravelTimeCalculator.compute(
                    rstate["pos"],      # meters
                    task["location"],   # meters
                    max_speed           # m/s
                )  # returns seconds

                est = rstate["time"] + travel_time  # seconds
                eet = est + task["duration"]  # seconds

            
                for res in task.get("uses_resources", []):
                    if res in resource_free_at:
                        res_free_time = resource_free_at[res]  # seconds
                        if est < res_free_time - TimeComparison.EPS:
                            est = res_free_time  # seconds

                    eet = est + task["duration"]  # seconds

                candidates.append((eet, est, rid))

            if not candidates:
                self.failure_reason = "capability_mismatch"
                return None

            candidates.sort(key=lambda x: x[0])
            num_candidates = min(3, len(candidates))
            selected_candidate = random.choice(candidates[:num_candidates])
            best_end, best_start, best_rid = selected_candidate


            task_deadline = task["deadline"]  # seconds
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

            robot_state[best_rid]["tasks"].append({
                "task_id": tid,
                "start_time": float(best_start),  # seconds
                "end_time": float(best_end),       # seconds
                "duration": float(task["duration"]),  # seconds
                "location": list(task["location"]),   # meters
            })
            robot_state[best_rid]["time"] = best_end  # seconds
            robot_state[best_rid]["pos"] = tuple(task["location"])  # meters

            for res in task.get("uses_resources", []):
                if res in self.resources:
                    resource_oh = ResourceOverheadCalculator.compute(
                        self.resources[res]["traversal_time"]
                    )
                    resource_free_time = best_end + resource_oh  # seconds
                    resource_free_at[res] = resource_free_time

        schedules = {
            rid: robot_state[rid]["tasks"] for rid in robot_ids
        }

        resource_allocation: Dict[str, List[Dict[str, Any]]] = {}
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
                            "start_time": task_entry["start_time"],  # seconds
                            "end_time": task_entry["end_time"],       # seconds
                            "resource_hold_duration": (
                                task_entry["end_time"] - task_entry["start_time"] + resource_oh
                            ),  # seconds
                        })
            resource_allocation[res].sort(key=lambda x: x["start_time"])

        makespan = 0.0  # seconds
        for rid in robot_ids:
            if schedules[rid]:
                completion = schedules[rid][-1]["end_time"]  # seconds
                makespan = max(makespan, completion)

        for res_name, allocations in resource_allocation.items():
            mutex_ok = TimeConstraintValidator.check_resource_mutex(allocations)
            if not mutex_ok:
                self.failure_reason = f"resource_mutex_violated: {res_name}"
                return None

        return {
            "feasible": True,
            "optimal": False,
            "status": "greedy",
            "solver_time": time.time() - t0,  # seconds
            "makespan": makespan,  # seconds
            "schedules": schedules,
            "resource_allocation": resource_allocation,
            "global_deadline": self.global_deadline,  # seconds
            "num_robots": len(robot_ids),
            "num_tasks": len(task_ids),
            "time_calculation_method": "TravelTimeCalculator (unified)",
            "time_units": "seconds",
            "spatial_units": "meters",
            "speed_units": "m/s",
        }



if __name__ == "__main__":
    import yaml

    print("=" * 70)
    print("MODIFIED GREEDY SCHEDULER - TEST")
    print("=" * 70)

    try:
        with open("config_warehouse_3x6.yaml", "r") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print("Config file not found. Creating a minimal config...")
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

    print("\n[Running greedy scheduler...]")
    scheduler = GreedyScheduler(config)
    result = scheduler.solve()

    if result:
        print(f"\n✓ Scheduling succeeded!")
        print(f"  Feasible: {result['feasible']}")
        print(f"  Makespan: {result['makespan']:.2f} {result['time_units']}")
        print(f"  Solver time: {result['solver_time']*1000:.2f} ms")
        print(f"  Time calculation: {result['time_calculation_method']}")
        print(f"\n  Schedule details:")
        for robot_id, tasks in result["schedules"].items():
            print(f"    Robot {robot_id}: {len(tasks)} tasks")
            for task in tasks:
                print(f"      - {task['task_id']}: "
                      f"[{task['start_time']:.2f}, {task['end_time']:.2f}]")
    else:
        print(f"\n✗ Scheduling failed!")
        print(f"  Reason: {scheduler.failure_reason}")

    print("\n" + "=" * 70)
