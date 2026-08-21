import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def tiny_config():
    return {
        "global_deadline": 100.0,
        "robots": [
            {
                "id": "robot_1",
                "capabilities": ["transport"],
                "max_speed": 1.0,
                "start_position": [0.0, 0.0],
            },
            {
                "id": "robot_2",
                "capabilities": ["transport"],
                "max_speed": 1.0,
                "start_position": [0.0, 0.0],
            },
        ],
        "tasks": [
            {
                "id": "task_1",
                "location": [0.0, 0.0],
                "duration": 5.0,
                "deadline": 100.0,
                "requires_capability": "transport",
                "uses_resources": ["corridor_A"],
            },
            {
                "id": "task_2",
                "location": [10.0, 0.0],
                "duration": 5.0,
                "deadline": 100.0,
                "requires_capability": "transport",
                "uses_resources": ["corridor_A"],
            },
        ],
        "resources": {
            "corridor_A": {
                "type": "mutex",
                "traversal_time": 2.0,
            }
        },
    }


def valid_schedule():
    return {
        "schedules": {
            "robot_1": [
                {
                    "task_id": "task_1",
                    "start_time": 0.0,
                    "end_time": 5.0,
                    "duration": 5.0,
                    "location": [0.0, 0.0],
                },
                {
                    "task_id": "task_2",
                    "start_time": 15.0,
                    "end_time": 20.0,
                    "duration": 5.0,
                    "location": [10.0, 0.0],
                },
            ],
            "robot_2": [],
        },
        "resource_allocation": {
            "corridor_A": [
                {
                    "robot": "robot_1",
                    "task_id": "task_1",
                    "start_time": 0.0,
                    "end_time": 7.0,
                },
                {
                    "robot": "robot_1",
                    "task_id": "task_2",
                    "start_time": 15.0,
                    "end_time": 22.0,
                },
            ]
        },
        "global_deadline": 100.0,
    }


class VerifyExperimentTests(unittest.TestCase):
    def test_valid_schedule_has_no_violations(self):
        from synasc2026.experiments.verify_experiment import validate_schedule

        violations = validate_schedule(tiny_config(), valid_schedule())

        self.assertEqual([], violations)

    def test_travel_gap_violation_is_reported(self):
        from synasc2026.experiments.verify_experiment import validate_schedule

        schedule = valid_schedule()
        schedule["schedules"]["robot_1"][1]["start_time"] = 10.0

        violations = validate_schedule(tiny_config(), schedule)

        self.assertTrue(any("travel_gap" in item for item in violations))

    def test_resource_mutex_violation_is_reported(self):
        from synasc2026.experiments.verify_experiment import validate_schedule

        schedule = valid_schedule()
        schedule["resource_allocation"]["corridor_A"][1]["start_time"] = 6.0

        violations = validate_schedule(tiny_config(), schedule)

        self.assertTrue(any("resource_mutex" in item for item in violations))


if __name__ == "__main__":
    unittest.main()
