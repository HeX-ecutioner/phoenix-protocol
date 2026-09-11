# Phoenix Protocol — Backend Engine

The backend for Phoenix Protocol is an adaptive, agentic network security compliance auditor for heterogeneous network-device configurations.

## Architecture

```text
HTTP multipart upload
        ↓
Flask API (backend/app/api/)
        ↓
run_scan() (backend/app/services/scanner.py)
        ↓
Cisco-like Parser (backend/app/parsers/)
        ↓
NormalizedConfig (backend/app/models/)
        ↓
Deterministic Compliance Engine (backend/app/rules/)
        ↓
NET-001 through NET-010 Rule Evaluations
        ↓
SQLite Persistence (phoenix_protocol.db)
        ↓
API Response / AI Intelligence Enrichment (backend/app/agents/)
```

### Core Separation of Concerns

> **"AI decides what the configuration means. Rules decide whether it is compliant. AI suggests how to remediate it."**

- **Deterministic Rules (`backend/app/rules/`)**: The sole authoritative source for compliance verdicts (`pass`, `fail`, `warning`), severity, and compliance scores ($0.0 \dots 100.0\%$).
- **AI / ADK Agents (`backend/app/agents/`)**:
  - **Teach-the-Auditor (`teach_auditor.py`)**: Interprets unfamiliar network configuration syntax and proposes rule mappings.
  - **Finding Explainer (`explanation.py`)**: Contextualizes deterministic findings into plain-language risk explanations.
  - **Remediation Agent (`remediation.py`)**: Proposes vendor-specific advisory fixes (`requires_human_approval = True`).
- **Knowledge Layer (`backend/knowledge/`)**: Isolated SQLite knowledge repository and approval state machine (`proposed` → `approved` / `rejected`), adapted via `backend/app/agents/knowledge.py`.

---

## Directory Structure

```text
backend/
├── app/                  # Core application package
│   ├── agents/           # Google ADK agent intelligence layer
│   ├── api/              # Flask application factory and REST endpoints
│   ├── database/         # SQLite persistence repository and schema
│   ├── models/           # Pydantic and dataclass models
│   ├── parsers/          # Network configuration parsers
│   ├── rules/            # Deterministic compliance rules (NET-001..NET-010)
│   ├── security/         # Secret redaction and evidence sanitization
│   └── services/         # Scanner and compliance calculation services
├── knowledge/            # Persistent Teach-the-Auditor knowledge layer
│   ├── models/           # KnowledgeMapping models
│   ├── services/         # KnowledgeService approval workflow
│   ├── storage/          # SQLite knowledge repository
│   ├── validation/       # Command normalization and secret sanitization
│   └── tests/            # Knowledge layer test suite
├── examples/             # Executable demos (phoenix_end_to_end_demo.py)
├── sample_data/          # Comprehensive QA and demo configuration fixtures
├── tests/                # Automated pytest test suite (177 tests)
├── .env.example          # Environment variable template
├── .flake8               # Flake8 linter configuration
├── pyrightconfig.json    # Pyright type checker configuration
└── requirements.txt      # Python runtime and test dependencies
```

---

## Installation & Setup

All backend commands should be run from the `backend/` directory:

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Running the API Server

From the `backend/` directory:

```bash
flask --app "app.api:create_app()" run --port 5000
```

Or programmatically in Python:
```python
from app.api import create_app

app = create_app()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
```

---

## Running Tests

From the `backend/` directory:

```bash
# Run full backend test suite
python -m pytest -v

# Run targeted AI and knowledge layer test suites
python -m pytest -v tests/test_teach_auditor.py
python -m pytest -v tests/test_ai_integration.py
python -m pytest -v knowledge/tests

# Bytecode compilation check
python -m compileall app tests knowledge
```

---

## End-to-End Demo

Run the self-contained 13-step terminal demonstration illustrating deterministic scanning, finding explanations, advisory remediation, unfamiliar command interpretation, human approval, and cached knowledge retrieval:

```bash
python examples/phoenix_end_to_end_demo.py
```

---

## API Endpoints

### 1. `GET /health`
Returns service operational health metadata.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "phoenix-protocol",
  "version": "1.0.0"
}
```

### 2. `POST /scan`
Uploads one or more network device configuration files and triggers deterministic compliance analysis.

- **Content-Type**: `multipart/form-data`
- **Form Parameters**:
  - `file` or `files`: One or more configuration files (up to 10 MB each).
  - `device_type` (optional): Requested device profile (default: `cisco_ios`).

**Response (201 Created):** Standard Phoenix Protocol scan JSON payload containing device findings, evidence snippets, compliance score, and summary statistics.

### 3. `GET /scan/<scan_id>`
Retrieves a previously evaluated scan by its unique scan ID directly from SQLite persistence.
