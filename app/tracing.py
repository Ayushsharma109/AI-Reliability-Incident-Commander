
import json
import time
import uuid
from datetime import datetime, timezone

from app.database import get_connection


def current_time():
    return datetime.now(timezone.utc).isoformat()


def create_run():
    run_id = str(uuid.uuid4())

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO workflow_runs
                (run_id, status, started_at)
            VALUES (?, ?, ?)
            """,
            (run_id, "running", current_time()),
        )

    return run_id


def add_step(
    run_id,
    step_name,
    input_data,
    output_data=None,
    status="success",
    duration_ms=None,
    error=None,
):
    with get_connection() as conn:
        run = conn.execute(
            "SELECT run_id FROM workflow_runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()

        if run is None:
            raise ValueError("Workflow run not found")

        conn.execute(
            """
            INSERT INTO trace_steps (
                run_id, step_name, input_data, output_data,
                status, duration_ms, error, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                step_name,
                json.dumps(input_data),
                json.dumps(output_data),
                status,
                duration_ms,
                error,
                current_time(),
            ),
        )

        if status == "failed":
            conn.execute(
                """
                UPDATE workflow_runs
                SET status = 'failed'
                WHERE run_id = ?
                """,
                (run_id,),
            )


def execute_traced_step(run_id, step_name, input_data, operation):
    start_time = time.perf_counter()

    try:
        output_data = operation()
        duration_ms = (time.perf_counter() - start_time) * 1000

        add_step(
            run_id=run_id,
            step_name=step_name,
            input_data=input_data,
            output_data=output_data,
            status="success",
            duration_ms=duration_ms,
        )

        return output_data

    except Exception as exc:
        duration_ms = (time.perf_counter() - start_time) * 1000

        add_step(
            run_id=run_id,
            step_name=step_name,
            input_data=input_data,
            output_data=None,
            status="failed",
            duration_ms=duration_ms,
            error=f"{type(exc).__name__}: {exc}",
        )

        raise


def finish_run(run_id):
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE workflow_runs
            SET status = CASE
                WHEN status = 'failed' THEN 'failed'
                ELSE 'completed'
            END,
            finished_at = ?
            WHERE run_id = ?
            """,
            (current_time(), run_id),
        )


def get_run_trace(run_id):
    with get_connection() as conn:
        run = conn.execute(
            "SELECT * FROM workflow_runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()

        if run is None:
            return None

        steps = conn.execute(
            """
            SELECT * FROM trace_steps
            WHERE run_id = ?
            ORDER BY step_id
            """,
            (run_id,),
        ).fetchall()

        return {
            "run": dict(run),
            "steps": [dict(step) for step in steps],
        }