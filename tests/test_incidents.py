
from fastapi.testclient import TestClient

from app.main import app


def test_incident_endpoint_detects_failed_workflow():
    with TestClient(app) as client:
        # Create a new workflow run
        run_response = client.post("/runs")
        assert run_response.status_code == 200

        run_data = run_response.json()
        run_id = run_data.get("run_id")

        assert run_id

        # Add a deliberately failed step
        step_response = client.post(
            f"/runs/{run_id}/steps",
            json={
                "step_name": "rank_jobs",
                "input_data": {"jobs_count": 2},
                "output_data": None,
                "status": "failed",
                "duration_ms": 5,
                "error": "ValueError: Job skill data is missing",
            },
        )

        assert step_response.status_code == 200

        # Finish the run
        finish_response = client.post(
            f"/runs/{run_id}/finish"
        )
        assert finish_response.status_code == 200

        # Verify incident detection
        incident_response = client.get(
            f"/runs/{run_id}/incident"
        )
        assert incident_response.status_code == 200

        incident_data = incident_response.json()

        assert incident_data["incident_detected"] is True
        assert incident_data["failed_step_count"] == 1
        assert len(incident_data["incidents"]) >= 1
