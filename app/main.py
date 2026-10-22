
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.database import initialize_database
from app.tracing import (
    create_run,
    add_step,
    finish_run,
    get_run_trace,
    execute_traced_step,
)
import json
from app.regression import (
    generate_regression_case,
    list_regression_cases,
)
from app.ranking import rank_jobs as calculate_job_ranking
from app.metrics import get_reliability_metrics
from app.llm_analyst import analyze_incident as run_llm_analysis
from app.evaluation import evaluate_analysis

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="AI Reliability & Incident Commander",
    version="0.1.0",
    lifespan=lifespan,
)


class StepRequest(BaseModel):
    step_name: str = Field(min_length=1, max_length=100)
    input_data: dict
    output_data: dict | None = None
    status: str = "success"
    duration_ms: float | None = Field(default=None, ge=0)
    error: str | None = None


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/runs")
def start_run():
    run_id = create_run()
    return {"run_id": run_id, "status": "running"}


@app.post("/runs/{run_id}/steps")
def record_step(run_id: str, step: StepRequest):
    if step.status not in {"success", "failed"}:
        raise HTTPException(
            status_code=400,
            detail="Status must be success or failed",
        )

    try:
        add_step(run_id, **step.model_dump())
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail="Workflow run not found",
        )

    return {"message": "Trace step recorded", "run_id": run_id}


@app.post("/runs/{run_id}/finish")
def complete_run(run_id: str):
    trace = get_run_trace(run_id)

    if trace is None:
        raise HTTPException(status_code=404, detail="Run not found")

    finish_run(run_id)
    return {"run_id": run_id, "status": "completed"}


@app.get("/runs/{run_id}")
def inspect_run(run_id: str):
    trace = get_run_trace(run_id)

    if trace is None:
        raise HTTPException(status_code=404, detail="Run not found")

    return trace




@app.post("/demo-run")
def demo_run():
    run_id = create_run()

    # Shared state for this workflow run
    state = {
        "jobs": [],
        "ranked_jobs": [],
        "candidate_skills": ["Python", "SQL", "RAG"],
    }

    def search_jobs():
        jobs = [
            {
                "title": "AI Intern",
                "required_skills": ["Python", "RAG", "SQL"],
            },
            {
                "title": "ML Intern",
                "required_skills": ["Python", "SQL", "Docker"],
            },
            {
                "title": "Backend Intern",
                "required_skills": ["Python", "FastAPI", "SQL"],
            },
        ]

        # Save search results in shared state
        state["jobs"] = jobs

        return {"jobs": jobs}

    def rank_jobs_operation():
        # Consume the output produced by search_jobs
        if not state["jobs"]:
            raise ValueError(
                "Cannot rank jobs: search results are missing"
            )

        ranked = calculate_job_ranking(
            jobs=state["jobs"],
            candidate_skills=state["candidate_skills"],
        )

        state["ranked_jobs"] = ranked

        return {"ranked_jobs": ranked}

    try:
        execute_traced_step(
            run_id=run_id,
            step_name="search_jobs",
            input_data={"query": "AI internships"},
            operation=search_jobs,
        )

        execute_traced_step(
            run_id=run_id,
            step_name="rank_jobs",
            input_data={
                "candidate_skills": state["candidate_skills"],
            },
            operation=rank_jobs_operation,
        )

    except Exception:
        # The tracing layer records the failed step.
        # Keep the API response available for trace inspection.
        pass

    finally:
        finish_run(run_id)

    return {
        "run_id": run_id,
        "workflow_status": "completed"
        if state["ranked_jobs"]
        else "failed",
        "ranked_jobs": state["ranked_jobs"],
    }

@app.get("/runs/{run_id}/incident")
def analyze_incident(run_id: str):
    trace = get_run_trace(run_id)

    if trace is None:
        raise HTTPException(
            status_code=404,
            detail="Run not found",
        )

    failed_steps = [
        step for step in trace["steps"]
        if step["status"] == "failed"
    ]

    incidents = []

    for step in failed_steps:
        error = step.get("error") or "Unknown error"
        error_lower = error.lower()

        
        previous_steps = [
            item for item in trace["steps"]
            if item["step_id"] < step["step_id"]
        ]

        previous_step = previous_steps[-1] if previous_steps else None

        previous_output = None

        if previous_step:
            try:
                previous_output = json.loads(
                    previous_step["output_data"]
                )
            except (TypeError, json.JSONDecodeError):
                previous_output = previous_step["output_data"]


        if "missing" in error_lower:
            diagnosis = (
                "Required data may be missing "
                "before this step."
            )
            recommendation = (
                "Validate required input fields "
                "before running this step."
            )

        elif "timeout" in error_lower:
            diagnosis = (
                "The operation may have exceeded "
                "its allowed execution time."
            )
            recommendation = (
                "Check service latency, timeout "
                "settings, and retry behaviour."
            )

        else:
            diagnosis = (
                "The step failed, but the root cause "
                "is not identified by current rules."
            )
            recommendation = (
                "Inspect the error and the preceding "
                "step's output."
            )

        try:
            parsed_input = json.loads(step["input_data"])
        except (TypeError, json.JSONDecodeError):
            parsed_input = step["input_data"]

        incidents.append({
            "step_id": step["step_id"],
            "step_name": step["step_name"],
            "error": error,
            "duration_ms": step["duration_ms"],
            "input_evidence": parsed_input,
            "root_cause_hypothesis": diagnosis,
            "recommended_action": recommendation,
            "previous_step_name": (
    previous_step["step_name"] if previous_step else None
),
"previous_step_output": previous_output,
        })

    return {
        "run_id": run_id,
        "workflow_status": trace["run"]["status"],
        "incident_detected": len(incidents) > 0,
        "failed_step_count": len(incidents),
        "incidents": incidents,
    }


@app.post("/runs/{run_id}/steps/{step_id}/regression-case")
def create_regression_case(run_id: str, step_id: int):
    try:
        case = generate_regression_case(run_id, step_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return case


@app.get("/regression-cases")
def get_regression_cases():
    return {"cases": list_regression_cases()}

@app.get("/metrics")
def reliability_metrics():
    return get_reliability_metrics()


@app.post("/runs/{run_id}/ai-incident-analysis")
def ai_incident_analysis(run_id: str):
    trace = get_run_trace(run_id)

    if trace is None:
        raise HTTPException(
            status_code=404,
            detail="Run not found",
        )

    failed_steps = [
        step for step in trace["steps"]
        if step["status"] == "failed"
    ]

    if not failed_steps:
        raise HTTPException(
            status_code=400,
            detail="This workflow has no failed steps",
        )

    incident_context = {
        "run_id": run_id,
        "workflow_status": trace["run"]["status"],
        "failed_steps": failed_steps,
        "all_steps": trace["steps"],
    }

    try:
        analysis = run_llm_analysis(incident_context)
        evaluation = evaluate_analysis(analysis, incident_context)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        )

    return {
    "run_id": run_id,
    "analysis_type": "llm_assisted",
    "analysis": analysis,
    "evaluation": evaluation,
}
