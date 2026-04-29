#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import json
import statistics
from typing import Dict, List, Any
import sys

try:
    from step3_modified_greedy import GreedyScheduler
    from step4_modified_smt_solver import HeterogeneousScheduler as SMTScheduler
except ImportError as e:
    print(f" {e}")
    print()
    sys.exit(1)

def get_test_config_simple():
    return {
        "global_deadline": 150.0,
        "robots": [
            {
                "id": "A",
                "name": "Robot A",
                "capabilities": ["basic"],
                "max_speed": 0.5,
                "start_position": [0.0, 0.0]
            }
        ],
        "tasks": [
            {
                "id": "task1",
                "location": [5.0, 0.0],
                "duration": 10.0,
                "deadline": 60.0,
                "requires_capability": "basic",
                "uses_resources": []
            },
            {
                "id": "task2",
                "location": [10.0, 0.0],
                "duration": 15.0,
                "deadline": 100.0,
                "requires_capability": "basic",
                "uses_resources": []
            }
        ],
        "resources": {}
    }


def get_test_config_medium():
    return {
        "global_deadline": 200.0,
        "robots": [
            {
                "id": "A",
                "capabilities": ["heavy"],
                "max_speed": 0.5,
                "start_position": [0.0, 0.0]
            },
            {
                "id": "B",
                "capabilities": ["light"],
                "max_speed": 1.0,
                "start_position": [0.0, 5.0]
            },
            {
                "id": "C",
                "capabilities": ["light", "heavy"],
                "max_speed": 0.7,
                "start_position": [5.0, 5.0]
            }
        ],
        "tasks": [
            {
                "id": "t1",
                "location": [5.0, 0.0],
                "duration": 15.0,
                "deadline": 100.0,
                "requires_capability": "heavy",
                "uses_resources": []
            },
            {
                "id": "t2",
                "location": [10.0, 0.0],
                "duration": 10.0,
                "deadline": 80.0,
                "requires_capability": "light",
                "uses_resources": []
            },
            {
                "id": "t3",
                "location": [8.0, -5.0],
                "duration": 12.0,
                "deadline": 90.0,
                "requires_capability": "light",
                "uses_resources": []
            },
            {
                "id": "t4",
                "location": [0.0, 10.0],
                "duration": 20.0,
                "deadline": 120.0,
                "requires_capability": "heavy",
                "uses_resources": []
            },
            {
                "id": "t5",
                "location": [5.0, 5.0],
                "duration": 8.0,
                "deadline": 70.0,
                "requires_capability": "light",
                "uses_resources": []
            },
            {
                "id": "t6",
                "location": [-5.0, 5.0],
                "duration": 18.0,
                "deadline": 130.0,
                "requires_capability": None,
                "uses_resources": []
            }
        ],
        "resources": {}
    }

def run_greedy_experiment(config: Dict[str, Any], num_runs: int = 50) -> List[Dict[str, Any]]:
    print(f"\n{'='*70}")
    print(f"Greedy ({num_runs})")
    print(f"{'='*70}")

    results = []

    for i in range(num_runs):
        if (i + 1) % 10 == 0:
            print(f"  [{i+1}/{num_runs}] ")

        t0 = time.time()
        scheduler = GreedyScheduler(config)
        schedule = scheduler.solve()
        elapsed = time.time() - t0

        if schedule and schedule.get("feasible"):
            results.append({
                "run_id": i,
                "feasible": True,
                "makespan": schedule.get("makespan", 0.0),
                "solver_time": elapsed,
                "num_robots": schedule.get("num_robots", 0),
                "num_tasks": schedule.get("num_tasks", 0),
                "calculation_method": schedule.get("time_calculation_method", "unknown"),
            })
        else:
            results.append({
                "run_id": i,
                "feasible": False,
                "makespan": None,
                "solver_time": elapsed,
                "failure_reason": scheduler.failure_reason if scheduler else "unknown",
            })

    return results


def run_smt_experiment(config: Dict[str, Any], num_runs: int = 50) -> List[Dict[str, Any]]:
  
    print(f"\n{'='*70}")
    print(f"SMT ({num_runs} )")
    print(f"{'='*70}")

    results = []

    for i in range(num_runs):
        if (i + 1) % 10 == 0:
            print(f"  [{i+1}/{num_runs}]")

        t0 = time.time()
        try:
            scheduler = SMTScheduler(config)
            schedule = scheduler.solve()
            elapsed = time.time() - t0

            if schedule and schedule.get("feasible"):
                results.append({
                    "run_id": i,
                    "feasible": True,
                    "optimal": schedule.get("optimal", False),
                    "makespan": schedule.get("makespan", 0.0),
                    "solver_time": elapsed,
                    "num_robots": schedule.get("num_robots", 0),
                    "num_tasks": schedule.get("num_tasks", 0),
                    "calculation_method": schedule.get("time_calculation_method", "unknown"),
                })
            else:
                results.append({
                    "run_id": i,
                    "feasible": False,
                    "optimal": False,
                    "makespan": None,
                    "solver_time": elapsed,
                    "failure_reason": scheduler.failure_reason if scheduler else "unknown",
                })
        except Exception as e:
            results.append({
                "run_id": i,
                "feasible": False,
                "optimal": False,
                "makespan": None,
                "solver_time": time.time() - t0,
                "failure_reason": str(e),
            })

    return results



def analyze_results(greedy_results: List[Dict], smt_results: List[Dict]) -> Dict[str, Any]:
    """Analyze and compare results."""

    greedy_feasible = sum(1 for r in greedy_results if r.get("feasible"))
    smt_feasible = sum(1 for r in smt_results if r.get("feasible"))

    greedy_makespans = [r["makespan"] for r in greedy_results if r.get("feasible")]
    smt_makespans = [r["makespan"] for r in smt_results if r.get("feasible")]

    greedy_times = [r["solver_time"] * 1000 for r in greedy_results]  # convert to ms
    smt_times = [r["solver_time"] * 1000 for r in smt_results]

    analysis = {
        "total_runs": len(greedy_results),

        "greedy": {
            "feasible_count": greedy_feasible,
            "feasible_rate": greedy_feasible / len(greedy_results) * 100,
            "avg_makespan": statistics.mean(greedy_makespans) if greedy_makespans else None,
            "min_makespan": min(greedy_makespans) if greedy_makespans else None,
            "max_makespan": max(greedy_makespans) if greedy_makespans else None,
            "std_makespan": statistics.stdev(greedy_makespans) if len(greedy_makespans) > 1 else 0,
            "avg_time_ms": statistics.mean(greedy_times),
            "min_time_ms": min(greedy_times),
            "max_time_ms": max(greedy_times),
        },

        "smt": {
            "feasible_count": smt_feasible,
            "feasible_rate": smt_feasible / len(smt_results) * 100,
            "avg_makespan": statistics.mean(smt_makespans) if smt_makespans else None,
            "min_makespan": min(smt_makespans) if smt_makespans else None,
            "max_makespan": max(smt_makespans) if smt_makespans else None,
            "std_makespan": statistics.stdev(smt_makespans) if len(smt_makespans) > 1 else 0,
            "avg_time_ms": statistics.mean(smt_times),
            "min_time_ms": min(smt_times),
            "max_time_ms": max(smt_times),
        },
    }

    if greedy_makespans and smt_makespans:
        improvements = [
            (g - s) / g * 100
            for g, s in zip(greedy_makespans, smt_makespans)
        ]
        analysis["comparison"] = {
            "smt_better_count": sum(1 for imp in improvements if imp > 0),
            "avg_improvement_percent": statistics.mean(improvements),
            "max_improvement_percent": max(improvements),
            "speedup_ratio": statistics.mean(greedy_times) / statistics.mean(smt_times) if smt_times else 0,
        }

    return analysis


def print_results(analysis: Dict[str, Any]):
    """Print analysis results."""

    print(f"\n{'='*70}")
    print("实验结果摘要")
    print(f"{'='*70}\n")

    print("[Greedy Scheduler]")
    print(f"  Feasible runs: {analysis['greedy']['feasible_count']}/{analysis['total_runs']} "
          f"({analysis['greedy']['feasible_rate']:.1f}%)")
    print(f"  Makespan (feasible):")
    if analysis['greedy']['avg_makespan']:
        print(f"    - Mean: {analysis['greedy']['avg_makespan']:.2f} s")
        print(f"    - Min: {analysis['greedy']['min_makespan']:.2f} s")
        print(f"    - Max: {analysis['greedy']['max_makespan']:.2f} s")
        print(f"    - Std: {analysis['greedy']['std_makespan']:.2f} s")
    print(f"  Solver time:")
    print(f"    - Mean: {analysis['greedy']['avg_time_ms']:.2f} ms")
    print(f"    - Min: {analysis['greedy']['min_time_ms']:.2f} ms")
    print(f"    - Max: {analysis['greedy']['max_time_ms']:.2f} ms")

    print(f"\n[SMT Solver]")
    print(f"  Feasible runs: {analysis['smt']['feasible_count']}/{analysis['total_runs']} "
          f"({analysis['smt']['feasible_rate']:.1f}%)")
    print(f"  Makespan (feasible):")
    if analysis['smt']['avg_makespan']:
        print(f"    - Mean: {analysis['smt']['avg_makespan']:.2f} s")
        print(f"    - Min: {analysis['smt']['min_makespan']:.2f} s")
        print(f"    - Max: {analysis['smt']['max_makespan']:.2f} s")
        print(f"    - Std: {analysis['smt']['std_makespan']:.2f} s")
    print(f"  Solver time:")
    print(f"    - Mean: {analysis['smt']['avg_time_ms']:.2f} ms")
    print(f"    - Min: {analysis['smt']['min_time_ms']:.2f} ms")
    print(f"    - Max: {analysis['smt']['max_time_ms']:.2f} ms")

    if "comparison" in analysis:
        print(f"\n[Comparison Results]")
        print(f"  SMT better: {analysis['comparison']['smt_better_count']}/{analysis['total_runs']}")
        print(f"  Mean improvement: {analysis['comparison']['avg_improvement_percent']:.2f}%")
        print(f"  Max improvement: {analysis['comparison']['max_improvement_percent']:.2f}%")
        speedup = analysis['comparison']['speedup_ratio']
        if speedup > 1:
            print(f"  Greedy speed: {speedup:.1f}x over SMT")
        else:
            print(f"  SMT speed: {1/speedup:.1f}x over Greedy")


def save_results_to_file(analysis: Dict[str, Any], filename: str = "experiment_results.json"):
    """Save results to file."""
    with open(filename, "w") as f:
        json.dump(analysis, f, indent=2)
    print(f"\nResults saved to: {filename}")

