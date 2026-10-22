
import json
import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2"


def analyze_incident(incident_context: dict) -> dict:
    prompt = f"""
You are a careful AI reliability engineer.

Analyze the workflow incident using only the supplied evidence.
Distinguish observed facts from inferred causes.
Never invent logs or facts.

Estimate confidence in your ROOT-CAUSE HYPOTHESIS:
- 0.0: no supporting evidence
- 0.3: weak or ambiguous evidence
- 0.6: plausible explanation supported by some evidence
- 0.8: strong evidence supports the explanation
- 0.95: direct, highly specific evidence supports the explanation

Confidence is a subjective assessment, NOT a calibrated probability.
Do not return zero when the evidence clearly supports a plausible hypothesis.
If evidence is insufficient, return low confidence and request human review.

Return ONLY valid JSON:
{{
  "root_cause_hypothesis": "string",
  "evidence": ["specific facts from the trace"],
  "recommended_actions": ["actionable steps"],
  "confidence": 0.0,
  "needs_human_review": true
}}

Incident evidence:
{json.dumps(incident_context, indent=2)}
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a careful AI incident analyst. "
                            "Return valid JSON only."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "format": "json",
                "options": {"temperature": 0},
            },
            timeout=120,
        )
        response.raise_for_status()

        content = response.json()["message"]["content"]
        result = json.loads(content)

        required_keys = {
            "root_cause_hypothesis",
            "evidence",
            "recommended_actions",
            "confidence",
            "needs_human_review",
        }

        if not isinstance(result, dict) or not required_keys.issubset(result):
            raise ValueError("LLM response is missing required fields")

        if not isinstance(result["confidence"], (int, float)):
            raise ValueError("Confidence must be numeric")

        if not 0 <= result["confidence"] <= 1:
            raise ValueError("Confidence must be between 0 and 1")

        if not isinstance(result["evidence"], list):
            raise ValueError("Evidence must be a list")

        if not isinstance(result["recommended_actions"], list):
            raise ValueError("Recommended actions must be a list")

        if not isinstance(result["needs_human_review"], bool):
            raise ValueError("needs_human_review must be boolean")

        if not isinstance(result["root_cause_hypothesis"], str):
            raise ValueError("Root cause hypothesis must be a string")

        if not all(
            isinstance(item, str) for item in result["evidence"]
        ):
            raise ValueError("Every evidence item must be a string")

        if not all(
            isinstance(item, str)
            for item in result["recommended_actions"]
        ):
            raise ValueError("Every recommended action must be a string")

        # An empty evidence list must never be presented
        # as an evidence-backed diagnosis.
        if not result["evidence"]:
            result["needs_human_review"] = True
            result["confidence"] = 0.0

        return result

    except requests.RequestException as exc:
        raise RuntimeError(
            f"Could not communicate with Ollama: {exc}"
        ) from exc
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            "Ollama returned an invalid response"
        ) from exc
