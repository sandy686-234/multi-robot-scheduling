from pathlib import Path
import json


SCHEDULE_PATH = Path(
    "artifacts/paper_verification/6r12t/seed_100/veriros_smt/schedule.json"
)


def load_task_times(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    tasks = {}

    for robot_id, entries in data["schedules"].items():
        for entry in entries:
            tasks[entry["task_id"]] = {
                "robot": robot_id,
                "start": float(entry["start_time"]),
                "end": float(entry["end_time"]),
            }

    return data["precedence"], tasks


def validate_precedence(before, after, observed):
    before_end = observed[before]["end"]
    after_start = observed[after]["start"]
    margin = after_start - before_end

    return {
        "property": f"{before} -> {after}",
        "verdict": "VALID" if margin >= 0 else "VIOLATED",
        "margin": round(margin, 2),
        "diagnosis": None
        if margin >= 0
        else f"precedence violation: {before} finishes after {after} starts",
    }


precedence, plan = load_task_times(SCHEDULE_PATH)

before, after = "task_5", "task_7"

print("Plan:")
print(validate_precedence(before, after, plan))

valid_observed = dict(plan)
valid_observed[before] = dict(plan[before])
valid_observed[before]["end"] = 51.00

print("\nValid runtime delay:")
print(validate_precedence(before, after, valid_observed))

violated_observed = dict(plan)
violated_observed[before] = dict(plan[before])
violated_observed[before]["end"] = 54.50

print("\nRuntime violation:")
print(validate_precedence(before, after, violated_observed))