
import re



def _tokens(value):
    return set(re.findall(r"[a-z0-9]+", str(value).lower()))



def evaluate_analysis(analysis: dict, incident_context: dict) -> dict:
    """Audit LLM evidence against facts present in the incident trace."""

    steps = incident_context.get("all_steps", [])
    failed_steps = incident_context.get("failed_steps", [])

    facts = [
        incident_context.get("run_id", ""),
        incident_context.get("workflow_status", ""),
    ]

    
    for step in steps:
        facts.extend([
            step.get("step_name", ""),
            step.get("status", ""),
            step.get("error", "") or "",
            str(step.get("input_data", "")),
            str(step.get("output_data", "")),
        ])

    fact_tokens = _tokens(" ".join(facts))
    evidence = analysis.get("evidence", [])

    supported = []
    unsupported = []

    for item in evidence:
        evidence_tokens = _tokens(item)
        # Ignore very common, uninformative words.
        meaningful = evidence_tokens - {
            "the", "and", "for", "with", "from", "was",
            "were", "step", "status", "error", "failed",
        }

        overlap = meaningful & fact_tokens
        ratio = len(overlap) / len(meaningful) if meaningful else 0

        if ratio >= 0.25:
            supported.append(item)
        else:
            unsupported.append(item)

    total = len(evidence)
    score = len(supported) / total if total else 0.0

    return {
        "evidence_grounding_score": round(score, 2),
        "supported_evidence_count": len(supported),
        "unsupported_evidence": unsupported,
        "needs_human_review": (
            not failed_steps
            or not evidence
            or bool(unsupported)
            or analysis.get("needs_human_review", False)
        ),
        "evaluation_method": "lexical_overlap",
    }
