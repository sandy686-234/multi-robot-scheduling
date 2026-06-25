#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Diagnosis helpers for schedule artifacts."""

from typing import Any, Dict, Iterable, List


def normalise_resource_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Return a stable resource-allocation row independent of producer naming."""
    return {
        "resource": row.get("resource", ""),
        "robot": row.get("robot_id") or row.get("robot") or row.get("rid") or "",
        "task_id": row.get("task_id", ""),
        "start_time": float(row.get("start_time", 0.0)),
        "end_time": float(row.get("end_time", 0.0)),
    }


def mutex_violations(rows: Iterable[Dict[str, Any]], eps: float = 1e-9) -> List[str]:
    """Report overlapping allocations for each mutex resource."""
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        normalised = normalise_resource_row(row)
        grouped.setdefault(normalised["resource"], []).append(normalised)

    violations: List[str] = []
    for resource, allocations in grouped.items():
        allocations.sort(key=lambda item: (item["start_time"], item["end_time"]))
        for prev, cur in zip(allocations, allocations[1:]):
            if cur["start_time"] < prev["end_time"] - eps:
                violations.append(
                    f"{resource}: {prev['task_id']} ({prev['robot']}) overlaps "
                    f"{cur['task_id']} ({cur['robot']})"
                )
    return violations
