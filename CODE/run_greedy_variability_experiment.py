#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import json
import random
from typing import Dict, List, Any
import sys

try:
    from step3_modified_greedy import GreedyScheduler
except ImportError as e:
    print(f" Import failed: {e}")
    print("Please ensure step3_modified_greedy.py is in the same directory")
    sys.exit(1)


def generate_random_scenario(config: tuple, seed: int) -> Dict[str, Any]:
    """Generate a random scenario with given (num_robots, num_tasks) and seed."""
    num_robots, num_tasks = config
    random.seed(seed)


    global_deadline = 200.0 * (num_tasks / 6.0)

   
    all_capabilities = ["light", "heavy", "basic"]

    robots = []
    for i in range(num_robots):
        rid = f"R{i+1}"
        capabilities = random.sample(all_capabilities, random.randint(1, 3))
        max_speed = random.uniform(0.3, 1.5)  # m/s
        start_x = random.uniform(-10.0, 10.0)
        start_y = random.uniform(-10.0, 10.0)

        robots.append({
            "id": rid,
            "name": f"Robot {rid}",
            "capabilities": capabilities,
            "max_speed": max_speed,
            "start_position": [start_x, start_y]
        })

    tasks = []
    for i in range(num_tasks):
        tid = f"T{i+1}"
        location_x = random.uniform(-20.0, 20.0)
        location_y = random.uniform(-20.0, 20.0)
        duration = random.uniform(5.0, 25.0)  # seconds
        deadline = random.uniform(duration + 10.0, global_deadline * 0.8)
        requires_capability = random.choice(all_capabilities) if random.random() < 0.7 else None

        tasks.append({
            "id": tid,
            "location": [location_x, location_y],
            "duration": duration,
            "deadline": deadline,
            "requires_capability": requires_capability,
            "uses_resources": []
        })

    return {
        "global_deadline": global_deadline,
        "robots": robots,
        "tasks": tasks,
        "resources": {}
    }


def run_greedy_variability_experiment():
    print("="*80)
    print("  Greedy Variability Experiment: 4 configs × 10 seeds")
    print("="*80)
    print()

    configs = [(2,4), (3,6), (4,8), (5,10)]
    seeds = range(100, 110)

    all_results = {}

    total_runs = len(configs) * len(seeds)
    run_count = 0

    for config in configs:
        num_robots, num_tasks = config
        config_key = f"{num_robots}x{num_tasks}"
        print(f"\n Testing config: {config_key} ({num_robots} robots, {num_tasks} tasks)")

        config_results = []

        for seed in seeds:
            run_count += 1
            print(f"  [{run_count}/{total_runs}] Seed {seed}...")

            scenario = generate_random_scenario(config, seed)

            t0 = time.time()
            scheduler = GreedyScheduler(scenario, seed=seed)
            schedule = scheduler.solve()
            elapsed = time.time() - t0

            result = {
                "config": config_key,
                "seed": seed,
                "feasible": schedule.get("feasible", False) if schedule else False,
                "makespan": schedule.get("makespan", None) if schedule else None,
                "solver_time": elapsed,
                "failure_reason": scheduler.failure_reason if not schedule else None
            }

            config_results.append(result)

        all_results[config_key] = config_results

    print(f"\n{'='*80}")
    print("EXPERIMENT RESULTS SUMMARY")
    print(f"{'='*80}\n")

    summary = {}

    for config_key, results in all_results.items():
        feasible_results = [r for r in results if r["feasible"]]
        makespans = [r["makespan"] for r in feasible_results]
        times = [r["solver_time"] * 1000 for r in results]  # ms

        summary[config_key] = {
            "total_runs": len(results),
            "feasible_count": len(feasible_results),
            "feasible_rate": len(feasible_results) / len(results) * 100,
            "avg_makespan": sum(makespans) / len(makespans) if makespans else None,
            "min_makespan": min(makespans) if makespans else None,
            "max_makespan": max(makespans) if makespans else None,
            "std_makespan": (sum((x - sum(makespans)/len(makespans))**2 for x in makespans) / len(makespans))**0.5 if len(makespans) > 1 else 0,
            "avg_time_ms": sum(times) / len(times),
            "min_time_ms": min(times),
            "max_time_ms": max(times),
        }

        print(f"[{config_key}]")
        print(f"  Feasible: {summary[config_key]['feasible_count']}/{summary[config_key]['total_runs']} "
              f"({summary[config_key]['feasible_rate']:.1f}%)")
        if makespans:
            print(f"  Makespan (s):")
            print(f"    - Mean: {summary[config_key]['avg_makespan']:.2f}")
            print(f"    - Min: {summary[config_key]['min_makespan']:.2f}")
            print(f"    - Max: {summary[config_key]['max_makespan']:.2f}")
            print(f"    - Std: {summary[config_key]['std_makespan']:.2f}")
        print(f"  Solver time (ms):")
        print(f"    - Mean: {summary[config_key]['avg_time_ms']:.2f}")
        print(f"    - Min: {summary[config_key]['min_time_ms']:.2f}")
        print(f"    - Max: {summary[config_key]['max_time_ms']:.2f}")
        print()


    output_file = "greedy_variability_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "experiment": "greedy_variability_4x10",
            "configs": configs,
            "seeds": list(seeds),
            "detailed_results": all_results,
            "summary": summary
        }, f, indent=2)

    print(f"Detailed results saved to: {output_file}")
    print(f"\n{'='*80}")
    print("EXPERIMENT COMPLETE!")
    print(f"{'='*80}")

    return summary


if __name__ == "__main__":
    run_greedy_variability_experiment()
