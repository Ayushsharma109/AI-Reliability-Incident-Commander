
import json
from pathlib import Path

from app.database import get_connection


CASES_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "regression_cases.json"
)


def generate_regression_case(run_id, step_id):
    with get_connection() as conn:
        step = conn.execute(
            """
            SELECT *
            FROM trace_steps
            WHERE run_id = ? AND step_id = ?
              AND status = 'failed'
            """,
            (run_id, step_id),
        ).fetchone()

    if step is None:
        raise ValueError("Failed trace step not found")

    try:
        input_data = json.loads(step["input_data"])
    except (TypeError, json.JSONDecodeError):
        input_data = step["input_data"]

    case = {
        "case_id": f"regression-{step['step_id']}",
        "source_run_id": run_id,
        "step_name": step["step_name"],
        "input_data": input_data,
        "original_error": step["error"],
        "expected_behavior": (
            "The step should handle this input "
            "without an unhandled exception."
        ),
        "status": "needs_review",
    }

    CASES_PATH.parent.mkdir(parents=True, exist_ok=True)

    if CASES_PATH.exists():
        cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    else:
        cases = []

    cases.append(case)

    CASES_PATH.write_text(
        json.dumps(cases, indent=2),
        encoding="utf-8",
    )

    return case


def list_regression_cases():
    if not CASES_PATH.exists():
        return []

    return json.loads(CASES_PATH.read_text(encoding="utf-8"))
