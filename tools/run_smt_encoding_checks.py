#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Run the hand-written SMT-LIB encoding checks with Z3."""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


EXPECTED = {
    "time_sat.smt2": "sat",
    "time_unsat.smt2": "unsat",
    "assignment_sat.smt2": "sat",
    "assignment_unsat.smt2": "unsat",
    "capability_sat.smt2": "sat",
    "capability_unsat.smt2": "unsat",
    "travel_ordering_sat.smt2": "sat",
    "travel_ordering_unsat.smt2": "unsat",
    "precedence_sat.smt2": "sat",
    "precedence_unsat.smt2": "unsat",
    "resource_mutex_sat.smt2": "sat",
    "resource_mutex_unsat.smt2": "unsat",
    "full_schedule_sat.smt2": "sat",
    "full_schedule_unsat.smt2": "unsat",
}


def first_result_line(stdout: str) -> str:
    for line in stdout.splitlines():
        line = line.strip()
        if line in {"sat", "unsat", "unknown"}:
            return line
    return ""


def run_checks(check_dir: Path, z3_bin: str) -> int:
    failures = []
    for name, expected in EXPECTED.items():
        path = check_dir / name
        if not path.exists():
            failures.append(f"{name}: missing file")
            continue

        proc = subprocess.run(
            [z3_bin, str(path)],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        actual = first_result_line(proc.stdout)
        ok = proc.returncode == 0 and actual == expected
        status = "OK" if ok else "FAIL"
        print(f"{status:4} {name:32} expected={expected:5} actual={actual or 'none'}")

        if not ok:
            failures.append(
                f"{name}: expected {expected}, got {actual or 'none'}; stderr={proc.stderr.strip()}"
            )

    if failures:
        print("\nSMT_ENCODING_CHECKS_FAILED")
        for failure in failures:
            print(failure)
        return 1

    print("\nSMT_ENCODING_CHECKS_OK")
    return 0


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-dir",
        default="smt_encoding_checks",
        help="Directory containing .smt2 encoding checks.",
    )
    parser.add_argument(
        "--z3",
        default=shutil.which("z3") or "/opt/homebrew/bin/z3",
        help="Path to the Z3 executable.",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv or sys.argv[1:])
    z3_bin = args.z3
    if not z3_bin or not Path(z3_bin).exists():
        print("Z3 executable not found. Install Z3 or pass --z3 /path/to/z3.")
        return 2
    return run_checks(Path(args.check_dir), z3_bin)


if __name__ == "__main__":
    raise SystemExit(main())
