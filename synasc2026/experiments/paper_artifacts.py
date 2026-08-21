#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Paper-oriented experiments and evidence artifacts for VeriROS.

This module keeps the experiment scenario, solver comparison, and artifact
generation on one path so the paper, code, and reproduced outputs stay aligned.
"""

import argparse
import csv
import json
import random
import statistics
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from synasc2026.diagnosis import mutex_violations, normalise_resource_row
from synasc2026.experiments.greedy_scheduler import GreedyScheduler
from synasc2026.scheduler import HAS_Z3, HeterogeneousScheduler as SMTScheduler


PAPER_CONFIGS: List[Tuple[int, int]] = [(3, 6), (6, 12), (7, 14), (8, 16)]
BASE_SEED = 100
DEFAULT_GREEDY_RUNS = 10
DEFAULT_SMT_RUNS = 3
DEFAULT_SMT_TIMEOUT_MS = 60_000


def generate_warehouse_config(num_robots: int, num_tasks: int, seed: int) -> Dict[str, Any]:
    """Generate a reproducible warehouse-style scenario with shared resources."""
    rng = random.Random(seed)
    area_size = 24.0 + num_tasks * 1.8
    global_deadline = 90.0 + num_tasks * 18.0 + num_robots * 8.0

    robot_profiles = [
        ("forklift", ["heavy_lift", "transport"], 0.78, [0.0, 0.0]),
        ("inspector", ["inspection", "transport"], 0.95, [area_size, 0.0]),
        ("charger", ["charging", "transport"], 0.82, [0.0, area_size]),
        ("carrier", ["transport", "inspection"], 1.08, [area_size, area_size]),
    ]

    robots = []
    for idx in range(num_robots):
        profile, capabilities, speed, base_position = robot_profiles[idx % len(robot_profiles)]
        jitter = [rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0)]
        robots.append({
            "id": f"robot_{idx + 1}",
            "name": f"{profile}_{idx + 1}",
            "capabilities": capabilities,
            "max_speed": round(max(0.45, speed + rng.uniform(-0.08, 0.08)), 2),
            "start_position": [
                round(min(max(base_position[0] + jitter[0], 0.0), area_size), 2),
                round(min(max(base_position[1] + jitter[1], 0.0), area_size), 2),
            ],
        })

    resources = {
        "corridor_A": {
            "type": "mutex",
            "traversal_time": 2.0,
            "rect": [area_size * 0.35, area_size * 0.42, area_size * 0.65, area_size * 0.58],
        },
        "loading_zone": {
            "type": "mutex",
            "traversal_time": 3.0,
            "rect": [area_size * 0.68, area_size * 0.15, area_size * 0.90, area_size * 0.36],
        },
        "charging_station": {
            "type": "mutex",
            "traversal_time": 2.5,
            "rect": [area_size * 0.08, area_size * 0.66, area_size * 0.28, area_size * 0.86],
        },
    }

    task_caps = ["transport", "heavy_lift", "inspection", "charging"]
    tasks = []
    for idx in range(num_tasks):
        capability = task_caps[idx % len(task_caps)]
        duration_base = {
            "transport": 6.0,
            "heavy_lift": 9.0,
            "inspection": 5.0,
            "charging": 7.0,
        }[capability]

        uses_resources: List[str] = []
        if idx % 2 == 0:
            uses_resources.append("corridor_A")
        if capability == "heavy_lift" or idx % 5 == 1:
            uses_resources.append("loading_zone")
        if capability == "charging":
            uses_resources.append("charging_station")

        tasks.append({
            "id": f"task_{idx + 1}",
            "location": [
                round(rng.uniform(area_size * 0.12, area_size * 0.88), 2),
                round(rng.uniform(area_size * 0.12, area_size * 0.88), 2),
            ],
            "duration": round(duration_base + rng.uniform(0.5, 3.5), 2),
            "deadline": global_deadline,
            "requires_capability": capability,
            "uses_resources": uses_resources,
        })

    precedence = [
        [f"task_{idx + 1}", f"task_{idx + 3}"]
        for idx in range(0, max(0, num_tasks - 2), 4)
    ]

    return {
        "scenario": "warehouse_shared_resource",
        "seed": seed,
        "global_deadline": round(global_deadline, 2),
        "robots": robots,
        "tasks": tasks,
        "resources": resources,
        "precedence": precedence,
    }


def _solver_slug(solver_name: str) -> str:
    return solver_name.lower().replace("-", "_").replace(" ", "_")


def _fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _normalise_resource_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return normalise_resource_row(row)


def _resource_rows(schedule: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    for resource, allocations in schedule.get("resource_allocation", {}).items():
        for allocation in allocations:
            row = dict(allocation)
            row["resource"] = resource
            rows.append(_normalise_resource_row(row))
    rows.sort(key=lambda item: (item["resource"], item["start_time"], item["end_time"]))
    return rows


def _mutex_violations(rows: Iterable[Dict[str, Any]]) -> List[str]:
    return mutex_violations(rows)


def write_schedule_artifacts(
    output_dir: Path,
    schedule: Dict[str, Any],
    solver_name: str,
    config_label: str,
    seed: int,
) -> None:
    """Write paper evidence files for one feasible schedule."""
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "solver": solver_name,
        "config_label": config_label,
        "seed": seed,
        "feasible": bool(schedule.get("feasible")),
        "status": schedule.get("status", "unknown"),
        "makespan": schedule.get("makespan"),
        "solver_time_sec": schedule.get("solver_time"),
    }
    schedule_doc = {
        "metadata": metadata,
        "schedules": schedule.get("schedules", {}),
        "resource_allocation": schedule.get("resource_allocation", {}),
        "precedence": schedule.get("precedence_edges", []),
        "global_deadline": schedule.get("global_deadline"),
        "time_units": schedule.get("time_units", "seconds"),
    }
    (output_dir / "schedule.json").write_text(
        json.dumps(schedule_doc, indent=2),
        encoding="utf-8",
    )

    result_lines = [
        f"solver: {solver_name}",
        f"config: {config_label}",
        f"seed: {seed}",
        f"status: {metadata['status']}",
        f"feasible: {metadata['feasible']}",
        f"makespan_sec: {_fmt(metadata['makespan'])}",
        f"solver_time_sec: {_fmt(metadata['solver_time_sec'])}",
    ]
    (output_dir / "z3_result.txt").write_text("\n".join(result_lines) + "\n", encoding="utf-8")

    rows = _resource_rows(schedule)
    with (output_dir / "mutex_trace.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["resource", "robot", "task_id", "start_time", "end_time"],
        )
        writer.writeheader()
        writer.writerows(rows)

    violations = _mutex_violations(rows)
    violation_text = "\n".join(violations) if violations else "No resource mutex violations detected."
    (output_dir / "violations.log").write_text(violation_text + "\n", encoding="utf-8")

    global_deadline = float(schedule.get("global_deadline") or 0.0)
    for robot_id, tasks in schedule.get("schedules", {}).items():
        trace_path = output_dir / f"trace_{robot_id}.csv"
        with trace_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "timestamp",
                    "robot_id",
                    "task_id",
                    "event",
                    "x",
                    "y",
                    "phi_mutex",
                    "phi_deadline",
                    "stl_rho",
                ],
            )
            writer.writeheader()
            for task in sorted(tasks, key=lambda item: item["start_time"]):
                x, y = task.get("location", [0.0, 0.0])
                deadline_rho = global_deadline - float(task["end_time"]) if global_deadline else 0.0
                for event, timestamp in (
                    ("start", task["start_time"]),
                    ("finish", task["end_time"]),
                ):
                    writer.writerow({
                        "timestamp": _fmt(float(timestamp), 6),
                        "robot_id": robot_id,
                        "task_id": task["task_id"],
                        "event": event,
                        "x": _fmt(float(x), 3),
                        "y": _fmt(float(y), 3),
                        "phi_mutex": "true" if not violations else "false",
                        "phi_deadline": "true" if deadline_rho >= -1e-9 else "false",
                        "stl_rho": _fmt(deadline_rho, 6),
                    })


def run_greedy(config: Dict[str, Any], seed: int) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    started = time.time()
    scheduler = GreedyScheduler(config, seed=seed)
    schedule = scheduler.solve()
    elapsed = time.time() - started
    if schedule and schedule.get("feasible"):
        schedule["solver_time"] = elapsed
        return {
            "solver": "Greedy",
            "seed": seed,
            "feasible": True,
            "status": schedule.get("status", "greedy"),
            "makespan": schedule.get("makespan"),
            "solver_time_sec": elapsed,
            "failure_reason": None,
        }, schedule

    return {
        "solver": "Greedy",
        "seed": seed,
        "feasible": False,
        "status": "failed",
        "makespan": None,
        "solver_time_sec": elapsed,
        "failure_reason": scheduler.failure_reason or "unknown",
    }, None


def run_smt(config: Dict[str, Any], seed: int, timeout_ms: int) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    if not HAS_Z3:
        return {
            "solver": "VeriROS-SMT",
            "seed": seed,
            "feasible": False,
            "status": "skipped",
            "makespan": None,
            "solver_time_sec": 0.0,
            "failure_reason": "z3_not_installed",
        }, None

    started = time.time()
    scheduler: Optional[SMTScheduler] = None
    try:
        scheduler = SMTScheduler(config, time_limit=timeout_ms)
        schedule = scheduler.solve()
    except Exception as exc:
        elapsed = time.time() - started
        return {
            "solver": "VeriROS-SMT",
            "seed": seed,
            "feasible": False,
            "status": "error",
            "makespan": None,
            "solver_time_sec": elapsed,
            "failure_reason": str(exc),
        }, None

    elapsed = time.time() - started
    if schedule and schedule.get("feasible"):
        schedule["solver_time"] = elapsed
        return {
            "solver": "VeriROS-SMT",
            "seed": seed,
            "feasible": True,
            "status": schedule.get("status", "sat"),
            "makespan": schedule.get("makespan"),
            "solver_time_sec": elapsed,
            "failure_reason": None,
        }, schedule

    reason = scheduler.failure_reason if scheduler else "unknown"
    status = "timeout" if reason and "timeout" in reason.lower() else "failed"
    return {
        "solver": "VeriROS-SMT",
        "seed": seed,
        "feasible": False,
        "status": status,
        "makespan": None,
        "solver_time_sec": elapsed,
        "failure_reason": reason or "unknown",
    }, None


def summarize_runs(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    feasible = [item for item in results if item["feasible"]]
    makespans = [float(item["makespan"]) for item in feasible if item["makespan"] is not None]
    times = [float(item["solver_time_sec"]) for item in results]
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


def run_experiment(
    output_dir: Path,
    configs: List[Tuple[int, int]],
    greedy_runs: int = DEFAULT_GREEDY_RUNS,
    smt_runs: int = DEFAULT_SMT_RUNS,
    base_seed: int = BASE_SEED,
    smt_timeout_ms: int = DEFAULT_SMT_TIMEOUT_MS,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    config_reports = []

    for num_robots, num_tasks in configs:
        label = f"{num_robots}r{num_tasks}t"
        greedy_results = []
        smt_results = []

        for offset in range(greedy_runs):
            seed = base_seed + offset
            config = generate_warehouse_config(num_robots, num_tasks, seed)
            result, schedule = run_greedy(config, seed)
            greedy_results.append(result)
            if schedule and offset == 0:
                write_schedule_artifacts(
                    output_dir / label / f"seed_{seed}" / _solver_slug("Greedy"),
                    schedule,
                    "Greedy",
                    label,
                    seed,
                )

        for offset in range(smt_runs):
            seed = base_seed + offset
            config = generate_warehouse_config(num_robots, num_tasks, seed)
            result, schedule = run_smt(config, seed, smt_timeout_ms)
            smt_results.append(result)
            if schedule and offset == 0:
                write_schedule_artifacts(
                    output_dir / label / f"seed_{seed}" / _solver_slug("VeriROS-SMT"),
                    schedule,
                    "VeriROS-SMT",
                    label,
                    seed,
                )

        summary = {
            "Greedy": summarize_runs(greedy_results),
            "VeriROS-SMT": summarize_runs(smt_results),
        }
        config_reports.append({
            "label": label,
            "num_robots": num_robots,
            "num_tasks": num_tasks,
            "runs": {
                "Greedy": greedy_results,
                "VeriROS-SMT": smt_results,
            },
            "summary": summary,
        })

    return {
        "experiment": "veriros_paper_shared_resource",
        "settings": {
            "configs": configs,
            "greedy_runs_per_config": greedy_runs,
            "smt_runs_per_config": smt_runs,
            "base_seed": base_seed,
            "smt_timeout_ms": smt_timeout_ms,
            "scenario_generator": "generate_warehouse_config",
            "shared_resources": ["corridor_A", "loading_zone", "charging_station"],
            "precedence_pattern": "task_{4k+1} precedes task_{4k+3}",
        },
        "configs": config_reports,
    }


def write_paper_summaries(summary_by_config: Dict[str, Dict[str, Dict[str, Any]]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for label, solver_items in summary_by_config.items():
        for solver, item in solver_items.items():
            rows.append({
                "config": label,
                "solver": solver,
                "runs": item.get("runs", 0),
                "feasible_runs": item.get("feasible_runs", 0),
                "feasible_rate": item.get("feasible_rate", 0.0),
                "avg_makespan_sec": item.get("avg_makespan"),
                "min_makespan_sec": item.get("min_makespan"),
                "max_makespan_sec": item.get("max_makespan"),
                "std_makespan_sec": item.get("std_makespan"),
                "avg_time_sec": item.get("avg_time_sec", item.get("avg_time")),
            })

    with (output_dir / "paper_results_summary.csv").open("w", newline="", encoding="utf-8") as file:
        fieldnames = [
            "config",
            "solver",
            "runs",
            "feasible_runs",
            "feasible_rate",
            "avg_makespan_sec",
            "min_makespan_sec",
            "max_makespan_sec",
            "std_makespan_sec",
            "avg_time_sec",
        ]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# VeriROS Paper Experiment Summary",
        "",
        "| Config | Solver | Feasible | Avg makespan (s) | Avg solve time (s) |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        feasible = f"{row['feasible_runs']}/{row['runs']}"
        lines.append(
            f"| {row['config']} | {row['solver']} | {feasible} | "
            f"{_fmt(row['avg_makespan_sec'], 2)} | {_fmt(row['avg_time_sec'], 4)} |"
        )
    lines.extend([
        "",
        "All configurations are generated by the same warehouse shared-resource generator.",
        "Each generated mission includes precedence edges of the form "
        "`task_{4k+1}` -> `task_{4k+3}`.",
        "The paper-facing artifact directories contain schedule.json, z3_result.txt, "
        "mutex_trace.csv, trace_robot_*.csv, and violations.log for representative runs.",
    ])
    (output_dir / "paper_results_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report_files(report: Dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "comparison_results_large_scale.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    rows = []
    for config in report["configs"]:
        for solver, runs in config["runs"].items():
            for run in runs:
                rows.append({
                    "config": config["label"],
                    "num_robots": config["num_robots"],
                    "num_tasks": config["num_tasks"],
                    "solver": solver,
                    "seed": run["seed"],
                    "feasible": run["feasible"],
                    "status": run["status"],
                    "makespan": run["makespan"],
                    "solver_time_sec": run["solver_time_sec"],
                    "failure_reason": run["failure_reason"],
                })

    with (output_dir / "comparison_results_large_scale.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=[
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
        ])
        writer.writeheader()
        writer.writerows(rows)

    summary_by_config = {
        config["label"]: config["summary"]
        for config in report["configs"]
    }
    write_paper_summaries(summary_by_config, output_dir)
    write_experiment_summary(report, output_dir / "EXPERIMENT_SUMMARY.md")


def write_experiment_summary(report: Dict[str, Any], output_path: Path) -> None:
    lines = [
        "# VeriROS Experiment Summary",
        "",
        "This artifact evaluates VeriROS on reproducible warehouse scheduling scenarios ",
        "with heterogeneous robots, shared mutex resources, precedence constraints, and deadlines.",
        "",
        "## Experimental Design",
        "",
        "- Scenario generator: `generate_warehouse_config` in `paper_artifacts.py`.",
        "- Baseline: randomized greedy scheduler.",
        "- VeriROS: SMT scheduler backed by Z3 when `z3-solver` is installed.",
        "- Shared resources: `corridor_A`, `loading_zone`, `charging_station`.",
        "- Precedence pattern: `task_{4k+1}` must finish before `task_{4k+3}` can start.",
        "- Representative evidence files are written under `<output-dir>/<config>/seed_<seed>/`.",
        "",
        "## Results",
        "",
        "| Config | Solver | Feasible | Avg makespan (s) | Avg solve time (s) | Status note |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for config in report["configs"]:
        for solver, item in config["summary"].items():
            feasible = f"{item['feasible_runs']}/{item['runs']}"
            notes = []
            if item.get("timeout_runs"):
                notes.append(f"{item['timeout_runs']} timeout")
            if solver == "VeriROS-SMT" and item["feasible_runs"] == 0:
                notes.append("SMT skipped or infeasible")
            lines.append(
                f"| {config['label']} | {solver} | {feasible} | "
                f"{_fmt(item['avg_makespan'], 2)} | {_fmt(item['avg_time_sec'], 4)} | "
                f"{'; '.join(notes) if notes else 'ok'} |"
            )

    lines.extend([
        "",
        "## Paper Alignment Notes",
        "",
        "- The Greedy and VeriROS-SMT runs now use the same scenario generator and seed policy.",
        "- The generated schedules include resource-allocation traces for checking mutex conflicts.",
        "- The generated schedules include precedence edges checked by the independent validator.",
        "- If `z3-solver` is missing, SMT rows are marked as skipped instead of being mixed with Greedy-only data.",
    ])
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run paper-aligned VeriROS experiments.")
    parser.add_argument("--output-dir", default="paper_artifacts", help="Directory for generated artifacts.")
    parser.add_argument("--quick", action="store_true", help="Run a fast smoke experiment.")
    parser.add_argument("--greedy-runs", type=int, default=DEFAULT_GREEDY_RUNS)
    parser.add_argument("--smt-runs", type=int, default=DEFAULT_SMT_RUNS)
    parser.add_argument("--smt-timeout-ms", type=int, default=DEFAULT_SMT_TIMEOUT_MS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configs = [(3, 6)] if args.quick else PAPER_CONFIGS
    greedy_runs = 2 if args.quick else args.greedy_runs
    smt_runs = 1 if args.quick else args.smt_runs

    report = run_experiment(
        Path(args.output_dir),
        configs=configs,
        greedy_runs=greedy_runs,
        smt_runs=smt_runs,
        smt_timeout_ms=args.smt_timeout_ms,
    )
    write_report_files(report, Path(args.output_dir))
    if not args.quick:
        write_report_files(report, Path("."))

    print("Experiment complete.")
    for config in report["configs"]:
        print(config["label"])
        for solver, item in config["summary"].items():
            feasible = f"{item['feasible_runs']}/{item['runs']}"
            print(
                f"  {solver}: feasible={feasible}, "
                f"avg_makespan={_fmt(item['avg_makespan'], 2)}s, "
                f"avg_time={_fmt(item['avg_time_sec'], 4)}s"
            )


if __name__ == "__main__":
    main()
