import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class SchedulerCorrectnessTests(unittest.TestCase):
    def test_ordering_variables_are_pruned_to_capable_task_pairs(self):
        from synasc2026.scheduler import HeterogeneousScheduler, generate_random_config

        expected_pruned_counts = {
            (3, 6): 44,
            (6, 12): 300,
            (7, 14): 608,
            (8, 16): 942,
        }

        for (num_robots, num_tasks), expected in expected_pruned_counts.items():
            with self.subTest(config=(num_robots, num_tasks)):
                cfg = generate_random_config(num_robots, num_tasks, seed=100)
                scheduler = HeterogeneousScheduler(cfg, time_limit=1000)

                self.assertTrue(scheduler.build_smt_model())
                self.assertEqual(expected, len(scheduler.vars["order"]))
                self.assertEqual(
                    num_robots * num_tasks * (num_tasks - 1),
                    scheduler.ordering_stats["full"],
                )
                self.assertEqual(expected, scheduler.ordering_stats["pruned"])

    def test_unsat_result_records_core_diagnosis(self):
        from synasc2026.scheduler import HeterogeneousScheduler

        cfg = {
            "global_deadline": 5.0,
            "robots": [
                {
                    "id": "R1",
                    "capabilities": ["basic"],
                    "max_speed": 1.0,
                    "start_position": [0.0, 0.0],
                }
            ],
            "tasks": [
                {
                    "id": "T1",
                    "location": [10.0, 0.0],
                    "duration": 1.0,
                    "deadline": 5.0,
                    "requires_capability": "basic",
                    "uses_resources": [],
                }
            ],
            "resources": {},
        }

        scheduler = HeterogeneousScheduler(cfg, time_limit=1000)

        self.assertIsNone(scheduler.solve())
        self.assertIsNotNone(scheduler.diagnosis)
        self.assertEqual("deadline_conflict", scheduler.diagnosis["category"])
        self.assertIn("deadline", scheduler.diagnosis["groups"])
        self.assertTrue(scheduler.unsat_core_labels)

    def test_greedy_resource_trace_end_time_includes_overhead(self):
        from synasc2026.experiments.greedy_scheduler import GreedyScheduler

        cfg = {
            "global_deadline": 100.0,
            "robots": [
                {
                    "id": "R1",
                    "capabilities": ["basic"],
                    "max_speed": 1.0,
                    "start_position": [0.0, 0.0],
                }
            ],
            "tasks": [
                {
                    "id": "T1",
                    "location": [0.0, 0.0],
                    "duration": 10.0,
                    "deadline": 100.0,
                    "requires_capability": "basic",
                    "uses_resources": ["corridor_A"],
                }
            ],
            "resources": {
                "corridor_A": {
                    "type": "mutex",
                    "traversal_time": 2.5,
                }
            },
        }

        schedule = GreedyScheduler(cfg, seed=1).solve()
        allocation = schedule["resource_allocation"]["corridor_A"][0]

        self.assertEqual(0.0, allocation["start_time"])
        self.assertEqual(12.5, allocation["end_time"])
        self.assertEqual(12.5, allocation["resource_hold_duration"])


if __name__ == "__main__":
    unittest.main()
