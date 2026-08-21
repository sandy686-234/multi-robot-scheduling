#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Independent validation for generated VeriROS experiment schedules."""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from synasc2026.experiments.paper_artifacts import (
    BASE_SEED,
    DEFAULT_GREEDY_RUNS,
    DEFAULT_SMT_RUNS,
    DEFAULT_SMT_TIMEOUT_MS,
    PAPER_CONFIGS,
    generate_warehouse_config,
    run_greedy,
    run_smt,
)
from synasc2026.validator import (
    ResourceOverheadCalculator,
    TimeComparison,
    TravelTimeCalculator,
)


def _task_map(config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {task["id"]: task for task in config.get("tasks", [])}


def _robot_map(config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {robot["id"]: robot for robot in config.get("robots", [])}


def _resource_map(config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return dict(config.get("resources", {}))


def _fmt_context(context: str, message: str) -> str:
    return f"{context}: {message}" if context else message


def validate_schedule(
    config: Dict[str, Any],
    schedule: Dict[str, Any],
    context: str = "",
) -> List[str]:
    """Validate a schedule without using the SMT model that produced it."""
    violations: List[str] = []
    tasks = _task_map(config)
    robots = _robot_map(config)
    resources = _resource_map(config)
    task_to_assignment: Dict[str, Tuple[str, Dict[str, Any]]] = {}
    global_deadline = float(config.get("global_deadline", schedule.get("global_deadline", 1e9)))

    for robot_id, entries in schedule.get("schedules", {}).items():
        if robot_id not in robots:
            violations.append(_fmt_context(context, f"unknown_robot {robot_id}"))
            continue

        robot = robots[robot_id]
        sorted_entries = sorted(entries, key=lambda item: float(item["start_time"]))
        previous = None

        for entry in sorted_entries:
            task_id = entry.get("task_id")
            if task_id not in tasks:
                violations.append(_fmt_context(context, f"unknown_task {task_id}"))
                continue

            task = tasks[task_id]
            start_time = float(entry["start_time"])
            end_time = float(entry["end_time"])
            duration = float(task["duration"])

            if task_id in task_to_assignment:
                old_robot, _ = task_to_assignment[task_id]
                violations.append(
                    _fmt_context(context, f"duplicate_assignment task={task_id} robots={old_robot},{robot_id}")
                )
            task_to_assignment[task_id] = (robot_id, entry)

            required = task.get("requires_capability")
            if required and required not in robot.get("capabilities", []):
                violations.append(
                    _fmt_context(context, f"capability task={task_id} robot={robot_id} requires={required}")
                )

            if not TimeComparison.geq(start_time, 0.0):
                violations.append(_fmt_context(context, f"negative_start task={task_id} start={start_time:.6f}"))

            expected_end = start_time + duration
            if not TimeComparison.eq(end_time, expected_end, eps=1e-6):
                violations.append(
                    _fmt_context(
                        context,
                        f"duration task={task_id} expected_end={expected_end:.6f} actual_end={end_time:.6f}",
                    )
                )

            if not TimeComparison.leq(end_time, float(task["deadline"]), eps=1e-6):
                violations.append(
                    _fmt_context(context, f"task_deadline task={task_id} end={end_time:.6f}")
                )

            if not TimeComparison.leq(end_time, global_deadline, eps=1e-6):
                violations.append(
                    _fmt_context(context, f"global_deadline task={task_id} end={end_time:.6f}")
                )

            if previous is None:
                travel = TravelTimeCalculator.compute(
                    robot["start_position"],
                    task["location"],
                    float(robot["max_speed"]),
                )
                earliest_start = travel
                previous_task_id = "start"
            else:
                previous_task = tasks[previous["task_id"]]
                travel = TravelTimeCalculator.compute(
                    previous_task["location"],
                    task["location"],
                    float(robot["max_speed"]),
                )
                earliest_start = float(previous["end_time"]) + travel
                previous_task_id = previous["task_id"]

            if not TimeComparison.leq(earliest_start, start_time, eps=1e-6):
                violations.append(
                    _fmt_context(
                        context,
                        f"travel_gap robot={robot_id} from={previous_task_id} to={task_id} "
                        f"earliest={earliest_start:.6f} actual={start_time:.6f}",
                    )
                )

            previous = entry

    missing = sorted(set(tasks) - set(task_to_assignment))
    extra = sorted(set(task_to_assignment) - set(tasks))
    for task_id in missing:
        violations.append(_fmt_context(context, f"missing_assignment task={task_id}"))
    for task_id in extra:
        violations.append(_fmt_context(context, f"extra_assignment task={task_id}"))

    task_entries = {
        task_id: entry
        for task_id, (_, entry) in task_to_assignment.items()
    }
    seen_resource_pairs = set()
    for resource_name, allocations in schedule.get("resource_allocation", {}).items():
        if resource_name not in resources:
            violations.append(_fmt_context(context, f"unknown_resource {resource_name}"))
            continue

        overhead = ResourceOverheadCalculator.compute(
            float(resources[resource_name].get("traversal_time", 0.0))
        )
        sorted_allocations = sorted(allocations, key=lambda item: float(item["start_time"]))

        for allocation in sorted_allocations:
            task_id = allocation.get("task_id")
            seen_resource_pairs.add((resource_name, task_id))
            if task_id not in tasks or task_id not in task_entries:
                violations.append(
                    _fmt_context(context, f"resource_unknown_task resource={resource_name} task={task_id}")
                )
                continue

            task = tasks[task_id]
            task_entry = task_entries[task_id]
            if resource_name not in task.get("uses_resources", []):
                violations.append(
                    _fmt_context(context, f"resource_not_required resource={resource_name} task={task_id}")
                )

            expected_start = float(task_entry["start_time"])
            expected_end = float(task_entry["end_time"]) + overhead
            actual_start = float(allocation["start_time"])
            actual_end = float(allocation["end_time"])

            if not TimeComparison.eq(actual_start, expected_start, eps=1e-6):
                violations.append(
                    _fmt_context(
                        context,
                        f"resource_start resource={resource_name} task={task_id} "
                        f"expected={expected_start:.6f} actual={actual_start:.6f}",
                    )
                )
            if not TimeComparison.eq(actual_end, expected_end, eps=1e-6):
                violations.append(
                    _fmt_context(
                        context,
                        f"resource_end resource={resource_name} task={task_id} "
                        f"expected={expected_end:.6f} actual={actual_end:.6f}",
                    )
                )

        for left, right in zip(sorted_allocations, sorted_allocations[1:]):
            left_end = float(left["end_time"])
            right_start = float(right["start_time"])
            if not TimeComparison.leq(left_end, right_start, eps=1e-6):
                violations.append(
                    _fmt_context(
                        context,
                        f"resource_mutex resource={resource_name} left={left['task_id']} "
                        f"right={right['task_id']} left_end={left_end:.6f} right_start={right_start:.6f}",
                    )
                )

    for task_id, task in tasks.items():
        if task_id not in task_entries:
            continue
        for resource_name in task.get("uses_resources", []):
            if (resource_name, task_id) not in seen_resource_pairs:
                violations.append(
                    _fmt_context(context, f"missing_resource_allocation resource={resource_name} task={task_id}")
                )

    return violations


def _parse_config_label(label: str) -> Tuple[int, int]:
    match = re.fullmatch(r"(\d+)r(\d+)t", label)
    if not match:
        raise ValueError(f"Cannot parse config label: {label}")
    return int(match.group(1)), int(match.group(2))


def iter_schedule_artifacts(artifact_dir: Path) -> Iterable[Tuple[Path, Dict[str, Any], Dict[str, Any], str]]:
    for schedule_path in sorted(artifact_dir.glob("*r*t/seed_*/**/schedule.json")):
        data = json.loads(schedule_path.read_text(encoding="utf-8"))
        metadata = data.get("metadata", {})
        label = metadata.get("config_label") or schedule_path.parents[2].name
        seed_text = str(metadata.get("seed") or schedule_path.parents[1].name.replace("seed_", ""))
        num_robots, num_tasks = _parse_config_label(label)
        seed = int(seed_text)
        config = generate_warehouse_config(num_robots, num_tasks, seed)
        context = f"{label}/seed_{seed}/{schedule_path.parent.name}"
        yield schedule_path, config, data, context


def validate_artifact_dir(artifact_dir: Path) -> Tuple[int, List[str]]:
    count = 0
    violations: List[str] = []
    for _, config, schedule, context in iter_schedule_artifacts(artifact_dir):
        count += 1
        violations.extend(validate_schedule(config, schedule, context))
    if count == 0:
        violations.append(f"no_schedule_artifacts directory={artifact_dir}")
    return count, violations


def validate_rerun(
    configs: List[Tuple[int, int]],
    greedy_runs: int = DEFAULT_GREEDY_RUNS,
    smt_runs: int = DEFAULT_SMT_RUNS,
    base_seed: int = BASE_SEED,
    smt_timeout_ms: int = DEFAULT_SMT_TIMEOUT_MS,
) -> Tuple[int, List[str]]:
    count = 0
    violations: List[str] = []

    for num_robots, num_tasks in configs:
        label = f"{num_robots}r{num_tasks}t"
        for offset in range(greedy_runs):
            seed = base_seed + offset
            config = generate_warehouse_config(num_robots, num_tasks, seed)
            result, schedule = run_greedy(config, seed)
            context = f"{label}/seed_{seed}/greedy"
            if not schedule:
                violations.append(f"{context}: no_schedule reason={result.get('failure_reason')}")
                continue
            count += 1
            violations.extend(validate_schedule(config, schedule, context))

        for offset in range(smt_runs):
            seed = base_seed + offset
            config = generate_warehouse_config(num_robots, num_tasks, seed)
            result, schedule = run_smt(config, seed, smt_timeout_ms)
            context = f"{label}/seed_{seed}/veriros_smt"
            if not schedule:
                violations.append(f"{context}: no_schedule reason={result.get('failure_reason')}")
                continue
            count += 1
            violations.extend(validate_schedule(config, schedule, context))

    return count, violations


def _print_result(count: int, violations: List[str]) -> int:
    if violations:
        print("VALIDATION_FAILED")
        print(f"schedules_checked={count}")
        print(f"violations={len(violations)}")
        for violation in violations[:50]:
            print(violation)
        if len(violations) > 50:
            print(f"... {len(violations) - 50} more")
        return 1

    print(f"VALIDATION_OK schedules={count}")
    return 0


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Independently validate VeriROS experiment schedules."
    )
    parser.add_argument(
        "--artifact-dir",
        default="/private/tmp/veriros_full_test",
        help="Experiment artifact directory containing schedule.json files.",
    )
    parser.add_argument(
        "--rerun-all",
        action="store_true",
        help="Re-run the full paper experiment in memory and validate every generated schedule.",
    )
    parser.add_argument("--greedy-runs", type=int, default=DEFAULT_GREEDY_RUNS)
    parser.add_argument("--smt-runs", type=int, default=DEFAULT_SMT_RUNS)
    parser.add_argument("--smt-timeout-ms", type=int, default=DEFAULT_SMT_TIMEOUT_MS)
    return parser.parse_args(argv)


def main(argv: List[str] = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.rerun_all:
        count, violations = validate_rerun(
            PAPER_CONFIGS,
            greedy_runs=args.greedy_runs,
            smt_runs=args.smt_runs,
            smt_timeout_ms=args.smt_timeout_ms,
        )
    else:
        count, violations = validate_artifact_dir(Path(args.artifact_dir))
    return _print_result(count, violations)


if __name__ == "__main__":
    raise SystemExit(main())
