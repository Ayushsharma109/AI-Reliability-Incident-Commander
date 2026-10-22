
import json
import requests
import pytest

from app import llm_analyst


def mock_response(payload):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "message": {
                    "content": json.dumps(payload)
                }
            }

    return FakeResponse()


@pytest.fixture
def valid_analysis():
    return {
        "root_cause_hypothesis": "Missing job data",
        "evidence": ["Ranking input did not contain jobs"],
        "recommended_actions": ["Validate input before ranking"],
        "confidence": 0.8,
        "needs_human_review": False,
    }


def test_valid_llm_analysis(monkeypatch, valid_analysis):
    monkeypatch.setattr(
        llm_analyst.requests,
        "post",
        lambda *args, **kwargs: mock_response(valid_analysis),
    )

    result = llm_analyst.analyze_incident(
        {"failed_steps": [{"step_name": "rank_jobs"}]}
    )

    assert result["root_cause_hypothesis"] == "Missing job data"
    assert result["confidence"] == 0.8
    assert result["evidence"]
    assert result["recommended_actions"]


def test_empty_evidence_requires_review(monkeypatch, valid_analysis):
    valid_analysis["evidence"] = []

    monkeypatch.setattr(
        llm_analyst.requests,
        "post",
        lambda *args, **kwargs: mock_response(valid_analysis),
    )

    result = llm_analyst.analyze_incident({"failed_steps": []})

    assert result["needs_human_review"] is True
    assert result["confidence"] == 0.0


@pytest.mark.parametrize("confidence", [-0.1, 1.1, "high"])
def test_invalid_confidence_rejected(
    monkeypatch, valid_analysis, confidence
):
    valid_analysis["confidence"] = confidence

    monkeypatch.setattr(
        llm_analyst.requests,
        "post",
        lambda *args, **kwargs: mock_response(valid_analysis),
    )

    with pytest.raises((ValueError, RuntimeError)):
        llm_analyst.analyze_incident({"failed_steps": []})


def test_ollama_connection_failure(monkeypatch):
    def fail_request(*args, **kwargs):
        raise requests.ConnectionError("Ollama unavailable")

    monkeypatch.setattr(
        llm_analyst.requests, "post", fail_request
    )

    with pytest.raises(RuntimeError, match="communicate with Ollama"):
        llm_analyst.analyze_incident({"failed_steps": []})


def test_invalid_json_rejected(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"message": {"content": "not valid json"}}

    monkeypatch.setattr(
        llm_analyst.requests,
        "post",
        lambda *args, **kwargs: FakeResponse(),
    )

    with pytest.raises(RuntimeError, match="invalid response"):
        llm_analyst.analyze_incident({"failed_steps": []})
