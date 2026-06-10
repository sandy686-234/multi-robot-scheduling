import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class PaperArtifactTests(unittest.TestCase):
    def test_warehouse_config_has_shared_resources_and_capability_coverage(self):
        from synasc2026.experiments.paper_artifacts import generate_warehouse_config

        cfg = generate_warehouse_config(3, 6, seed=100)

        self.assertEqual(3, len(cfg["robots"]))
        self.assertEqual(6, len(cfg["tasks"]))
        self.assertGreaterEqual(len(cfg["resources"]), 2)
        self.assertTrue(any(t["uses_resources"] for t in cfg["tasks"]))

        robot_capabilities = {
            capability
            for robot in cfg["robots"]
            for capability in robot["capabilities"]
        }
        required_capabilities = {
            task["requires_capability"]
            for task in cfg["tasks"]
            if task.get("requires_capability")
        }
        self.assertTrue(required_capabilities.issubset(robot_capabilities))

    def test_schedule_artifacts_are_written(self):
        from synasc2026.experiments.paper_artifacts import write_schedule_artifacts

        fake_schedule = {
            "feasible": True,
            "status": "sat",
            "makespan": 12.0,
            "solver_time": 0.25,
            "schedules": {
                "robot_1": [
                    {
                        "task_id": "task_1",
                        "start_time": 1.0,
                        "end_time": 5.0,
                        "duration": 4.0,
                        "location": [1.0, 2.0],
                    }
                ]
            },
            "resource_allocation": {
                "corridor_A": [
                    {
                        "robot_id": "robot_1",
                        "task_id": "task_1",
                        "start_time": 1.0,
                        "end_time": 5.0,
                    }
                ]
            },
        }

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            write_schedule_artifacts(
                out_dir,
                fake_schedule,
                solver_name="VeriROS-SMT",
                config_label="3r6t",
                seed=100,
            )

            self.assertTrue((out_dir / "schedule.json").exists())
            self.assertTrue((out_dir / "z3_result.txt").exists())
            self.assertTrue((out_dir / "mutex_trace.csv").exists())
            self.assertTrue((out_dir / "violations.log").exists())
            self.assertTrue((out_dir / "trace_robot_1.csv").exists())

            schedule = json.loads((out_dir / "schedule.json").read_text())
            self.assertEqual("VeriROS-SMT", schedule["metadata"]["solver"])
            self.assertEqual("3r6t", schedule["metadata"]["config_label"])

            with (out_dir / "mutex_trace.csv").open(newline="") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual("corridor_A", rows[0]["resource"])

    def test_summary_files_are_written(self):
        from synasc2026.experiments.paper_artifacts import write_paper_summaries

        summary = {
            "3r6t": {
                "Greedy": {
                    "runs": 2,
                    "feasible_runs": 2,
                    "avg_makespan": 20.0,
                    "avg_time": 0.01,
                },
                "VeriROS-SMT": {
                    "runs": 1,
                    "feasible_runs": 1,
                    "avg_makespan": 15.0,
                    "avg_time": 0.2,
                },
            }
        }

        with tempfile.TemporaryDirectory() as tmp:
            write_paper_summaries(summary, Path(tmp))
            self.assertTrue((Path(tmp) / "paper_results_summary.csv").exists())
            markdown = (Path(tmp) / "paper_results_summary.md").read_text()
            self.assertIn("3r6t", markdown)
            self.assertIn("VeriROS-SMT", markdown)


if __name__ == "__main__":
    unittest.main()
