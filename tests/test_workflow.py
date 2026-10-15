
from fastapi.testclient import TestClient

from app.main import app


def test_demo_run_returns_ranked_jobs():
    with TestClient(app) as client:
        response = client.post("/demo-run")

    assert response.status_code == 200

    data = response.json()

    assert data["workflow_status"] == "completed"

    ranked_jobs = data["ranked_jobs"]

    assert len(ranked_jobs) == 3
    assert ranked_jobs[0]["title"] == "AI Intern"
    assert ranked_jobs[0]["match_score"] == 1.0

    scores = [job["match_score"] for job in ranked_jobs]
    assert scores == sorted(scores, reverse=True)
