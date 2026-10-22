
from app.evaluation import evaluate_analysis


def test_supported_evidence_passes():
    context = {
        "run_id": "run-1",
        "workflow_status": "failed",
        "failed_steps": [{"step_name": "rank_jobs"}],
        "all_steps": [
            {
                "step_name": "rank_jobs",
                "status": "failed",
                "error": "Required job data is missing",
            }
        ],
    }

    analysis = {
        "evidence": [
            "Required job data is missing before ranking"
        ],
        "needs_human_review": False,
    }

    result = evaluate_analysis(analysis, context)

    assert result["evidence_grounding_score"] == 1.0
    assert result["unsupported_evidence"] == []
    assert result["needs_human_review"] is False


def test_unsupported_evidence_requires_review():
    context = {
        "run_id": "run-1",
        "workflow_status": "failed",
        "failed_steps": [{"step_name": "rank_jobs"}],
        "all_steps": [
            {
                "step_name": "rank_jobs",
                "status": "failed",
                "error": "Required job data is missing",
            }
        ],
    }

    analysis = {
        "evidence": [
            "Database server crashed because of network congestion"
        ],
        "needs_human_review": False,
    }

    result = evaluate_analysis(analysis, context)

    assert result["evidence_grounding_score"] == 0.0
    assert len(result["unsupported_evidence"]) == 1
    assert result["needs_human_review"] is True


def test_empty_evidence_requires_review():
    result = evaluate_analysis(
        {"evidence": [], "needs_human_review": False},
        {
            "failed_steps": [{"step_name": "rank_jobs"}],
            "all_steps": [],
        },
    )

    assert result["evidence_grounding_score"] == 0.0
    assert result["needs_human_review"] is True
