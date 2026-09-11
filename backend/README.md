# Phoenix Protocol — Backend Engine

The backend for Phoenix Protocol is an adaptive, agentic network security compliance auditor for network-device configurations.

---

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
REST API Response / CSV Report / AI Intelligence Enrichment (backend/app/agents/)
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

## MVP Scope: Implemented vs Extensible

### Currently Implemented Support (Frozen & Authoritative)
- **Vendor & Device Support**: Cisco IOS (`cisco_ios` profile) configuration parsing.
- **Compliance Rules**: Deterministic rules `NET-001` through `NET-010` covering administrative access, encryption, authentication, logging, NTP, and security banners.
- **Scoring Engine**: Tested-rule compliance score formula: $\text{score} = \frac{\text{pass}}{\text{pass} + \text{fail}} \times 100\%$, with warnings, errors, and N/A excluded from denominator.
- **Evidence & Line Range**: Line-referenced configuration evidence with automatic credential/secret sanitization.
- **Persistence**: Parameterized SQLite storage (`scans`, `devices`, `rules`, `rule_results`).
- **Reports**: Deterministic, formula-injection-safe CSV export (`/api/scans/{scan_id}/report.csv`).
- **Security**: Secret redaction (`[REDACTED]`), zero raw config persistence, zero shell/exec/subprocess execution.
- **Local API**: Unauthenticated REST API for local hackathon integration.

### Architectural Extensibility (Future Milestones)
- **Multi-Vendor Expansion**: Parser abstraction (`NormalizedConfig`) is architecturally extensible to Cisco NX-OS, Juniper Junos, Arista EOS, and Palo Alto PAN-OS.
- **Enterprise Authentication & RBAC**: JWT, OAuth2, and multi-tenant access control.
- **Expanded Rule Frameworks**: Extension to full CIS Benchmark, NIST SP 800-53, and DISA STIG catalogs.
- **Active Device Retrieval**: Direct SSH/NETCONF collectors (intentionally disabled in MVP).

---

## Directory Structure

```text
backend/
├── app/                  # Core application package
│   ├── agents/           # Google ADK agent intelligence layer
│   ├── api/              # Flask REST endpoints and CORS adapter
│   ├── database/         # SQLite persistence repository and schema
│   ├── models/           # Pydantic and dataclass models
│   ├── parsers/          # Network configuration parsers
│   ├── rules/            # Deterministic compliance rules (NET-001..NET-010)
│   ├── security/         # Secret redaction and evidence sanitization
│   └── services/         # Scanner and compliance calculation services
├── examples/             # Executable demos and integration scripts
│   ├── phoenix_end_to_end_demo.py
│   ├── verify_integration_flow.py
│   └── run_live_http_verification.py
├── knowledge/            # Persistent Teach-the-Auditor knowledge layer
│   ├── models/           # KnowledgeMapping models
│   ├── services/         # KnowledgeService approval workflow
│   ├── storage/          # SQLite knowledge repository
│   ├── validation/       # Command normalization and secret sanitization
│   └── tests/            # Knowledge layer test suite
├── sample_data/          # Comprehensive QA and demo configuration fixtures
├── tests/                # Automated pytest test suite (195 tests)
│   ├── test_api_v2.py    # Authoritative /api/... REST contract test suite
│   ├── test_api.py       # Legacy API route test suite
│   └── ...
├── INTEGRATION_CONTRACT.md # Formal API contract specification for frontend
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

### CORS Configuration
By default, the backend allows local development origins (`http://localhost:5173`, `http://127.0.0.1:5173`, `http://localhost:3000`, `http://127.0.0.1:3000`).
To configure custom origins, set the environment variable:
```bash
export CORS_ALLOWED_ORIGINS="http://localhost:5173,http://127.0.0.1:5173"
```

---

## Running Tests

From the `backend/` directory:

```bash
# Run full backend test suite (194 passing)
python -m pytest -v

# Run new /api contract tests
python -m pytest -v tests/test_api_v2.py

# Bytecode compilation check
python -m compileall app tests knowledge
```

---

## Authoritative Frontend API Endpoints

All new frontend integrations target `/api/...`. Every endpoint returns a structured envelope:

```json
{
  "data": { ... },
  "error": null,
  "request_id": "req-..."
}
```

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/device-types` | Returns list of supported device profiles (`cisco_ios`). |
| `POST` | `/api/scans` | Multipart configuration upload and compliance scan execution. |
| `GET` | `/api/scans/{scan_id}` | Retrieves full persisted scan results and metrics. |
| `GET` | `/api/scans/{scan_id}/devices` | Lists devices evaluated in the scan. |
| `GET` | `/api/scans/{scan_id}/devices/{device_id}` | Retrieves complete device audit and rule findings. |
| `GET` | `/api/rules` | Retrieves catalog of active rules (`NET-001` through `NET-010`). |
| `GET` | `/api/rules/{rule_id}` | Retrieves metadata for a single compliance rule. |
| `GET` | `/api/scans/{scan_id}/report.csv` | Downloads spreadsheet-safe, sanitized CSV report. |
| `GET` | `/health` / `/api/health` | Service health status check. |

For detailed payloads, request parameters, and error responses, see [INTEGRATION_CONTRACT.md](INTEGRATION_CONTRACT.md).
