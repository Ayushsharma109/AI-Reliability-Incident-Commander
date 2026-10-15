
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "traces.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS workflow_runs (
                run_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS trace_steps (
                step_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                step_name TEXT NOT NULL,
                input_data TEXT,
                output_data TEXT,
                status TEXT NOT NULL,
                duration_ms REAL,
                error TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (run_id)
                    REFERENCES workflow_runs(run_id)
            )
        """)

        conn.commit()