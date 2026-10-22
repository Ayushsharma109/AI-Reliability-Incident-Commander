
from datetime import datetime

from app.database import get_connection


def get_reliability_metrics():
    conn = get_connection()

    try:
        # 1. Read workflow run statistics
        runs = conn.execute("""
            SELECT run_id, status, started_at, finished_at
            FROM workflow_runs
        """).fetchall()

        total_runs = len(runs)
        completed_runs = sum(
            1 for run in runs if run["status"] == "completed"
        )
        failed_runs = sum(
            1 for run in runs if run["status"] == "failed"
        )

        success_rate = (
            round(completed_runs / total_runs * 100, 2)
            if total_runs else 0.0
        )

        failure_rate = (
            round(failed_runs / total_runs * 100, 2)
            if total_runs else 0.0
        )

        # 2. Calculate workflow durations
        run_durations_ms = []

        for run in runs:
            if run["started_at"] and run["finished_at"]:
                try:
                    started = datetime.fromisoformat(run["started_at"])
                    finished = datetime.fromisoformat(run["finished_at"])

                    duration_ms = (
                        finished - started
                    ).total_seconds() * 1000

                    if duration_ms >= 0:
                        run_durations_ms.append(duration_ms)

                except (ValueError, TypeError):
                    # Skip invalid timestamps
                    continue

        average_run_duration_ms = (
            round(sum(run_durations_ms) / len(run_durations_ms), 2)
            if run_durations_ms else 0.0
        )

        # 3. Read step-level statistics
        step_stats = conn.execute("""
            SELECT
                step_name,
                COUNT(*) AS total_steps,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END)
                    AS failed_steps,
                AVG(duration_ms) AS average_duration_ms
            FROM trace_steps
            GROUP BY step_name
            ORDER BY failed_steps DESC, step_name ASC
        """).fetchall()

        total_steps = sum(
            row["total_steps"] for row in step_stats
        )

        failed_steps = sum(
            row["failed_steps"] for row in step_stats
        )

        average_step_latency_ms = (
            round(
                sum(
                    (row["average_duration_ms"] or 0)
                    * row["total_steps"]
                    for row in step_stats
                ) / total_steps,
                2,
            )
            if total_steps else 0.0
        )

        most_failing_steps = [
            {
                "step_name": row["step_name"],
                "total_steps": row["total_steps"],
                "failed_steps": row["failed_steps"],
                "failure_rate_percent": round(
                    row["failed_steps"] / row["total_steps"] * 100,
                    2,
                ),
                "average_duration_ms": round(
                    row["average_duration_ms"] or 0, 2
                ),
            }
            for row in step_stats
            if row["failed_steps"] > 0
        ]

        return {
            "workflow_metrics": {
                "total_runs": total_runs,
                "completed_runs": completed_runs,
                "failed_runs": failed_runs,
                "other_status_runs": (
                    total_runs - completed_runs - failed_runs
                ),
                "success_rate_percent": success_rate,
                "failure_rate_percent": failure_rate,
                "average_duration_ms": average_run_duration_ms,
            },
            "step_metrics": {
                "total_steps": total_steps,
                "failed_steps": failed_steps,
                "average_latency_ms": average_step_latency_ms,
                "most_failing_steps": most_failing_steps,
            },
        }

    finally:
        conn.close()
