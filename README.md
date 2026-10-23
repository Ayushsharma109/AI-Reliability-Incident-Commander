# Sentinel — AI Reliability & Incident Commander

An AI-assisted reliability monitoring and incident investigation platform for agentic workflows.

Sentinel traces workflow executions, tracks reliability metrics, investigates failed steps using a locally hosted LLM, evaluates evidence grounding, and generates regression cases to help prevent recurring failures.

## 🚀 Key Features

- **Workflow Tracing:** Record workflow runs, execution steps, statuses, errors, and durations.
- **Reliability Metrics:** Track success rate, failure rate, average run duration, and frequently failing steps.
- **AI-Assisted Incident Analysis:** Use Ollama with Llama 3.2 to generate root-cause hypotheses and recommended actions.
- **Evidence Grounding Evaluation:** Check whether incident evidence overlaps with facts recorded in the workflow trace.
- **Regression Case Generation:** Turn workflow failures into regression test cases.
- **REST API:** Interact with the platform through FastAPI endpoints.
- **Automated Testing:** Includes tests for workflow execution, metrics, ranking, incident analysis, and evaluation.

## 🧠 Architecture

```text
Workflow Execution
       |
       v
FastAPI Backend
       |
       v
SQLite Execution Traces
       |
       +------------------+
       |                  |
       v                  v
Reliability Metrics   Incident Detection
                          |
                          v
                  Local LLM Analysis
                   (Ollama / Llama 3.2)
                          |
                          v
                 Evidence Evaluation
                          |
                          v
                Regression Case Generation
                          |
                          v
                 Sentinel Dashboard
```

## 🛠️ Tech Stack

- Python
- FastAPI
- SQLite
- Ollama
- Llama 3.2
- HTML, CSS, JavaScript
- Pytest
- GitHub Actions

## ⚙️ Getting Started

### Prerequisites

- Python installed
- Ollama installed for local LLM analysis
- Git

### 1. Clone the repository

```bash
git clone https://github.com/Ayushsharma109/AI-Reliability-Incident-Commander
cd ai_reliability_incident_commander
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Start the local LLM

```powershell
ollama pull llama3.2
ollama run llama3.2
```

Keep Ollama running when using AI incident analysis.

### 5. Start the API and dashboard

```powershell
uvicorn app.main:app --reload
```

Open the dashboard:

http://127.0.0.1:8000/

API documentation:

http://127.0.0.1:8000/docs

## 🔌 API Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /health` | Check service health |
| `POST /demo-run` | Execute the demonstration workflow |
| `POST /runs` | Create a workflow run |
| `POST /runs/{run_id}/steps` | Record a workflow step |
| `POST /runs/{run_id}/finish` | Finish a workflow run |
| `GET /runs/{run_id}` | Inspect a workflow trace |
| `GET /runs/{run_id}/incident` | Retrieve incident information |
| `POST /runs/{run_id}/ai-incident-analysis` | Generate AI-assisted incident analysis |
| `GET /metrics` | Retrieve workflow and step metrics |
| `GET /regression-cases` | List generated regression cases |

## 🧪 Testing

Run the test suite:

```powershell
python -m pytest -v
```

The current test suite contains 18 passing tests covering workflow execution, job ranking, incident detection, LLM response validation, evidence evaluation, and reliability metrics.

## 🔍 Example Use Case

Imagine an AI job-search workflow fails during job ranking because the required job data is missing.

Sentinel can:

1. Record the failed execution step.
2. Expose the failure through the incident endpoint.
3. Ask a local LLM to propose a root-cause hypothesis.
4. Evaluate the generated evidence against the recorded trace.
5. Flag unsupported evidence for human review.
6. Generate a regression case to help test against similar failures.

## 🔐 Design Considerations

- Local LLM inference avoids requiring a paid hosted LLM API for incident analysis.
- Evidence evaluation is based on lexical overlap and is **not a guarantee of semantic correctness**.
- AI-generated root causes are hypotheses, not definitive diagnoses.
- Human review is important before applying remediation actions.

## 🗺️ Future Improvements

- Semantic evidence verification
- Historical incident clustering
- Workflow latency and failure trend visualizations
- Configurable alert thresholds
- Regression-case execution and automated remediation proposals
- Production deployment with authentication and access controls

## 👨‍💻 Author

Ayush Sharma

AI Engineering | Agentic AI | LLM Reliability | Workflow Observability
