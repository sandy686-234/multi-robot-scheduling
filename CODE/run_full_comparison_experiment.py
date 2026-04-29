#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Full Greedy vs SMT comparison experiment.

This script will:
1. Run Greedy scheduler (50 times)
2. Run SMT solver (50 times)
3. Compare results (quality, speed, feasibility)
4. Generate statistics and charts
5. Generate data tables for paper

Usage:
    python run_full_comparison_experiment.py
"""

import time
import json
import statistics
from typing import Dict, List, Any
import sys

try:
    from step3_modified_greedy import GreedyScheduler
    from step4_modified_smt_solver import HeterogeneousScheduler as SMTScheduler
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请确保 step3_modified_greedy.py 和 step4_modified_smt_solver.py 在同一目录")
    sys.exit(1)

# ============================================================
# Configuration and test cases
# ============================================================

def get_test_config_simple():
    """Simple config: 1 robot, 2 tasks."""
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
    """Medium config: 3 robots, 6 tasks."""
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


# ============================================================
# Experiment runner functions
# ============================================================

def run_greedy_experiment(config: Dict[str, Any], num_runs: int = 50) -> List[Dict[str, Any]]:
    """Run Greedy experiment."""
    print(f"\n{'='*70}")
    print(f"运行 Greedy 调度器 ({num_runs} 次)")
    print(f"{'='*70}")

    results = []

    for i in range(num_runs):
        if (i + 1) % 10 == 0:
            print(f"  [{i+1}/{num_runs}] 正在运行...")

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
    """Run SMT experiment."""
    print(f"\n{'='*70}")
    print(f"运行 SMT 求解器 ({num_runs} 次)")
    print(f"{'='*70}")

    results = []

    for i in range(num_runs):
        if (i + 1) % 10 == 0:
            print(f"  [{i+1}/{num_runs}] 正在运行...")

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


# ============================================================
# Analysis functions
# ============================================================

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

    print("【Greedy 调度器】")
    print(f"  可行次数: {analysis['greedy']['feasible_count']}/{analysis['total_runs']} "
          f"({analysis['greedy']['feasible_rate']:.1f}%)")
    print(f"  Makespan (可行解):")
    if analysis['greedy']['avg_makespan']:
        print(f"    - 平均: {analysis['greedy']['avg_makespan']:.2f} s")
        print(f"    - 最小: {analysis['greedy']['min_makespan']:.2f} s")
        print(f"    - 最大: {analysis['greedy']['max_makespan']:.2f} s")
        print(f"    - 标差: {analysis['greedy']['std_makespan']:.2f} s")
    print(f"  求解时间:")
    print(f"    - 平均: {analysis['greedy']['avg_time_ms']:.2f} ms")
    print(f"    - 最小: {analysis['greedy']['min_time_ms']:.2f} ms")
    print(f"    - 最大: {analysis['greedy']['max_time_ms']:.2f} ms")

    print(f"\n【SMT 求解器】")
    print(f"  可行次数: {analysis['smt']['feasible_count']}/{analysis['total_runs']} "
          f"({analysis['smt']['feasible_rate']:.1f}%)")
    print(f"  Makespan (可行解):")
    if analysis['smt']['avg_makespan']:
        print(f"    - 平均: {analysis['smt']['avg_makespan']:.2f} s")
        print(f"    - 最小: {analysis['smt']['min_makespan']:.2f} s")
        print(f"    - 最大: {analysis['smt']['max_makespan']:.2f} s")
        print(f"    - 标差: {analysis['smt']['std_makespan']:.2f} s")
    print(f"  求解时间:")
    print(f"    - 平均: {analysis['smt']['avg_time_ms']:.2f} ms")
    print(f"    - 最小: {analysis['smt']['min_time_ms']:.2f} ms")
    print(f"    - 最大: {analysis['smt']['max_time_ms']:.2f} ms")

    if "comparison" in analysis:
        print(f"\n【对比结果】")
        print(f"  SMT更优次数: {analysis['comparison']['smt_better_count']}/{analysis['total_runs']}")
        print(f"  平均质量改进: {analysis['comparison']['avg_improvement_percent']:.2f}%")
        print(f"  最大质量改进: {analysis['comparison']['max_improvement_percent']:.2f}%")
        speedup = analysis['comparison']['speedup_ratio']
        if speedup > 1:
            print(f"  Greedy速度: {speedup:.1f}x SMT")
        else:
            print(f"  SMT速度: {1/speedup:.1f}x Greedy")


def save_results_to_file(analysis: Dict[str, Any], filename: str = "experiment_results.json"):
    """Save results to file."""
    with open(filename, "w") as f:
        json.dump(analysis, f, indent=2)
    print(f"\n✅ 结果已保存到: {filename}")


# ============================================================
# Main
# ============================================================

def main():
    """Main entry point."""

    print("\n" + "="*70)
    print("  Greedy vs SMT 完整对比实验")
    print("="*70)
    print("""
这个实验将：
  1. 运行Greedy调度器 50次
  2. 运行SMT求解器 50次
  3. 对比结果（质量、速度、可行性）
  4. 生成统计数据供论文使用

预计耗时：5-10分钟
""")

    print("选择测试用例:")
    print("  1. 简单 (1机器人, 2任务)")
    print("  2. 中等 (3机器人, 6任务)")

    choice = input("请选择 (1 或 2): ").strip()

    if choice == "1":
        config = get_test_config_simple()
        test_name = "simple_1x2"
    elif choice == "2":
        config = get_test_config_medium()
        test_name = "medium_3x6"
    else:
        print("❌ 无效选择")
        return 1

    print(f"\n✓ 已选择: {test_name}")
    print(f"  机器人数: {len(config['robots'])}")
    print(f"  任务数: {len(config['tasks'])}")

    greedy_results = run_greedy_experiment(config, num_runs=50)
    smt_results = run_smt_experiment(config, num_runs=50)

    analysis = analyze_results(greedy_results, smt_results)

    print_results(analysis)

    save_results_to_file(analysis, f"experiment_results_{test_name}.json")

    print("\n" + "="*70)
    print("✅ 实验完成！")
    print("="*70)
    print(f"""
结果文件: experiment_results_{test_name}.json

后续步骤：
  1. 查看结果数据
  2. 在论文的Results部分添加对比结果
  3. 生成性能对比图表
  4. 投稿！
""")

    return 0


if __name__ == "__main__":
    exit(main())
