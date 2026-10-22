
import sqlite3

import pytest

from app import metrics


@pytest.fixture
def isolated_metrics_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test_metrics.db"

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    conn.executescript("""
        CREATE TABLE workflow_runs (
            run_id TEXT PRIMARY KEY,
            status TEXT,
            started_at TEXT,
            finished_at TEXT
        );

        CREATE TABLE trace_steps (
            step_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT,
            step_name TEXT,
            input_data TEXT,
            output_data TEXT,
            status TEXT,
            duration_ms REAL,
            error TEXT,
            created_at TEXT
        );

        INSERT INTO workflow_runs VALUES
        (
            'run-1',
            'completed',
            '2026-01-01T10:00:00+00:00',
            '2026-01-01T10:00:01+00:00'
        ),
        (
            'run-2',
            'failed',
            '2026-01-01T10:00:00+00:00',
            '2026-01-01T10:00:03+00:00'
        ),
        (
            'run-3',
            'running',
            '2026-01-01T10:00:00+00:00',
            NULL
        );

        INSERT INTO trace_steps
            (run_id, step_name, status, duration_ms, error)
        VALUES
            ('run-1', 'search_jobs', 'success', 10, NULL),
            ('run-1', 'rank_jobs', 'success', 20, NULL),
            ('run-2', 'rank_jobs', 'failed', 30, 'Missing skills');
    """)

    conn.commit()
    conn.close()

    def test_connection():
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        return connection

    monkeypatch.setattr(
        metrics,
        "get_connection",
        test_connection,
    )


def test_workflow_metrics_are_calculated_correctly(
    isolated_metrics_db,
):
    result = metrics.get_reliability_metrics()
    workflow = result["workflow_metrics"]

    assert workflow["total_runs"] == 3
    assert workflow["completed_runs"] == 1
    assert workflow["failed_runs"] == 1
    assert workflow["other_status_runs"] == 1

    assert workflow["success_rate_percent"] == pytest.approx(33.33, abs=0.01)
    assert workflow["failure_rate_percent"] == pytest.approx(33.33, abs=0.01)

    # Only completed runs with valid finish times contribute here.
    # The failed run also has a finish time, so both finished runs count.
    assert workflow["average_duration_ms"] == 2000.0


def test_step_latency_and_failing_step_are_correct(
    isolated_metrics_db,
):
    result = metrics.get_reliability_metrics()
    steps = result["step_metrics"]

    assert steps["total_steps"] == 3
    assert steps["failed_steps"] == 1
    assert steps["average_latency_ms"] == 20.0

    assert len(steps["most_failing_steps"]) == 1

    failing_step = steps["most_failing_steps"][0]

    assert failing_step["step_name"] == "rank_jobs"
    assert failing_step["total_steps"] == 2
    assert failing_step["failed_steps"] == 1
    assert failing_step["failure_rate_percent"] == 50.0


def test_empty_database_returns_zero_rates(tmp_path, monkeypatch):
    db_path = tmp_path / "empty_metrics.db"

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    conn.executescript("""
        CREATE TABLE workflow_runs (
            run_id TEXT PRIMARY KEY,
            status TEXT,
            started_at TEXT,
            finished_at TEXT
        );

        CREATE TABLE trace_steps (
            step_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT,
            step_name TEXT,
            input_data TEXT,
            output_data TEXT,
            status TEXT,
            duration_ms REAL,
            error TEXT,
            created_at TEXT
        );
    """)

    conn.commit()
    conn.close()

    def test_connection():
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        return connection

    monkeypatch.setattr(
        metrics,
        "get_connection",
        test_connection,
    )

    result = metrics.get_reliability_metrics()

    assert result["workflow_metrics"]["total_runs"] == 0
    assert result["workflow_metrics"]["success_rate_percent"] == 0.0
    assert result["workflow_metrics"]["failure_rate_percent"] == 0.0

    assert result["step_metrics"]["total_steps"] == 0
    assert result["step_metrics"]["average_latency_ms"] == 0.0
    assert result["step_metrics"]["most_failing_steps"] == []
