#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import json
import statistics
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from synasc2026.experiments.greedy_scheduler import GreedyScheduler
from synasc2026.experiments.paper_artifacts import generate_warehouse_config
from synasc2026.scheduler import (
    HAS_Z3,
    HeterogeneousScheduler as SMTScheduler,
)


BASELINE_CONFIG = (3, 6)
LARGE_SCALE_CONFIGS = [(6, 12), (7, 14), (8, 16)]

GREEDY_RUNS_PER_CONFIG = 10
SMT_RUNS_PER_CONFIG = 3
BASE_SEED = 100
SMT_TIMEOUT_MS = 60_000

RESULTS_DIR = Path(__file__).resolve().parent / "results"
RESULTS_JSON = RESULTS_DIR / "comparison_results_large_scale.json"
RESULTS_CSV = RESULTS_DIR / "comparison_results_large_scale.csv"


def run_greedy(config: Dict[str, Any], seed: int) -> Dict[str, Any]:
    started = time.time()
    scheduler = GreedyScheduler(config, seed=seed)
    schedule = scheduler.solve()
    elapsed = time.time() - started

    if schedule and schedule.get("feasible"):
        return {
            "solver": "greedy",
            "seed": seed,
            "feasible": True,
            "status": schedule.get("status", "greedy"),
            "makespan": schedule.get("makespan"),
            "solver_time_sec": elapsed,
            "failure_reason": None,
        }

    return {
        "solver": "greedy",
        "seed": seed,
        "feasible": False,
        "status": "failed",
        "makespan": None,
        "solver_time_sec": elapsed,
        "failure_reason": scheduler.failure_reason or "unknown",
    }


def run_smt(config: Dict[str, Any], seed: int) -> Dict[str, Any]:
    if not HAS_Z3:
        return {
            "solver": "smt",
            "seed": seed,
            "feasible": False,
            "status": "skipped",
            "makespan": None,
            "solver_time_sec": 0.0,
            "failure_reason": "z3_not_installed",
        }

    started = time.time()
    scheduler: Optional[SMTScheduler] = None
    try:
        scheduler = SMTScheduler(config, time_limit=SMT_TIMEOUT_MS)
        schedule = scheduler.solve()
    except Exception as exc:
        elapsed = time.time() - started
        return {
            "solver": "smt",
            "seed": seed,
            "feasible": False,
            "status": "error",
            "makespan": None,
            "solver_time_sec": elapsed,
            "failure_reason": str(exc),
        }

    elapsed = time.time() - started
    if schedule and schedule.get("feasible"):
        return {
            "solver": "smt",
            "seed": seed,
            "feasible": True,
            "status": schedule.get("status", "sat"),
            "makespan": schedule.get("makespan"),
            "solver_time_sec": elapsed,
            "failure_reason": None,
        }

    reason = scheduler.failure_reason if scheduler else "unknown"
    status = "timeout" if reason and "unknown" in reason.lower() else "failed"
    return {
        "solver": "smt",
        "seed": seed,
        "feasible": False,
        "status": status,
        "makespan": None,
        "solver_time_sec": elapsed,
        "failure_reason": reason or "unknown",
    }


def summarize(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    feasible = [item for item in results if item["feasible"]]
    makespans = [item["makespan"] for item in feasible if item["makespan"] is not None]
    times = [item["solver_time_sec"] for item in results]

    return {
        "runs": len(results),
        "feasible_runs": len(feasible),
        "feasible_rate": len(feasible) / len(results) if results else 0.0,
        "timeout_runs": sum(1 for item in results if item["status"] == "timeout"),
        "avg_makespan": statistics.mean(makespans) if makespans else None,
        "min_makespan": min(makespans) if makespans else None,
        "max_makespan": max(makespans) if makespans else None,
        "std_makespan": statistics.stdev(makespans) if len(makespans) > 1 else 0.0,
        "avg_time_sec": statistics.mean(times) if times else 0.0,
        "min_time_sec": min(times) if times else 0.0,
        "max_time_sec": max(times) if times else 0.0,
    }


def run_config(num_robots: int, num_tasks: int) -> Dict[str, Any]:
    label = f"{num_robots}r{num_tasks}t"
    print(f"\n[{label}]")

    greedy_results = []
    for offset in range(GREEDY_RUNS_PER_CONFIG):
        seed = BASE_SEED + offset
        config = generate_warehouse_config(num_robots, num_tasks, seed)
        greedy_results.append(run_greedy(config, seed))
    print(f"  Greedy runs: {len(greedy_results)}")

    smt_results = []
    for offset in range(SMT_RUNS_PER_CONFIG):
        seed = BASE_SEED + offset
        config = generate_warehouse_config(num_robots, num_tasks, seed)
        smt_results.append(run_smt(config, seed))
    print(f"  SMT runs:    {len(smt_results)}")

    summary = {
        "greedy": summarize(greedy_results),
        "smt": summarize(smt_results),
    }
    print_summary(summary)

    return {
        "label": label,
        "num_robots": num_robots,
        "num_tasks": num_tasks,
        "runs": {
            "greedy": greedy_results,
            "smt": smt_results,
        },
        "summary": summary,
    }


def print_summary(summary: Dict[str, Dict[str, Any]]) -> None:
    for solver_name in ("greedy", "smt"):
        item = summary[solver_name]
        feasible = f"{item['feasible_runs']}/{item['runs']}"
        rate = item["feasible_rate"] * 100
        avg_makespan = item["avg_makespan"]
        makespan_text = f"{avg_makespan:.2f}s" if avg_makespan is not None else "n/a"
        print(
            f"  {solver_name.upper():6} feasible={feasible:<5} "
            f"rate={rate:5.1f}% avg_makespan={makespan_text:<10} "
            f"avg_time={item['avg_time_sec']:.3f}s timeout={item['timeout_runs']}"
        )


def write_json(report: Dict[str, Any], output_path: Path) -> None:
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")


def write_csv(report: Dict[str, Any], output_path: Path) -> None:
    rows = []
    for config_result in report["configs"]:
        for solver_name, solver_runs in config_result["runs"].items():
            for run in solver_runs:
                rows.append({
                    "config": config_result["label"],
                    "num_robots": config_result["num_robots"],
                    "num_tasks": config_result["num_tasks"],
                    "solver": solver_name,
                    "seed": run["seed"],
                    "feasible": run["feasible"],
                    "status": run["status"],
                    "makespan": run["makespan"],
                    "solver_time_sec": run["solver_time_sec"],
                    "failure_reason": run["failure_reason"],
                })

    fieldnames = [
        "config",
        "num_robots",
        "num_tasks",
        "solver",
        "seed",
        "feasible",
        "status",
        "makespan",
        "solver_time_sec",
        "failure_reason",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    print("=" * 72)
    print("Greedy vs SMT scheduling experiment")
    print("=" * 72)
    print(f"Greedy runs per config: {GREEDY_RUNS_PER_CONFIG}")
    print(f"SMT runs per config:    {SMT_RUNS_PER_CONFIG}")
    print(f"SMT timeout:            {SMT_TIMEOUT_MS / 1000:.0f}s")

    configs = [BASELINE_CONFIG] + LARGE_SCALE_CONFIGS
    results = [run_config(num_robots, num_tasks) for num_robots, num_tasks in configs]

    report = {
        "experiment": "greedy_vs_smt_large_scale",
        "configs": results,
        "settings": {
            "baseline_config": BASELINE_CONFIG,
            "large_scale_configs": LARGE_SCALE_CONFIGS,
            "greedy_runs_per_config": GREEDY_RUNS_PER_CONFIG,
            "smt_runs_per_config": SMT_RUNS_PER_CONFIG,
            "base_seed": BASE_SEED,
            "smt_timeout_ms": SMT_TIMEOUT_MS,
        },
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    write_json(report, RESULTS_JSON)
    write_csv(report, RESULTS_CSV)
    print("\nSaved:")
    print(f"  {RESULTS_JSON}")
    print(f"  {RESULTS_CSV}")


if __name__ == "__main__":
    main()
