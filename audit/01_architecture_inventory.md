# Phoenix Protocol Backend Audit — Architecture Inventory

**Date of Audit**: 2026-09-12  
**Auditor**: Independent Backend Product Auditor  
**Audit Scope**: Phoenix Protocol Backend Engine  

---

## 1. Observed Repository Structure

The actual backend implementation lives entirely under `backend/`. The frontend is decoupled in `frontend/`.

```text
phoenix-protocol/
├── backend/
│   ├── app/                      # Authoritative application package
│   │   ├── agents/               # Google ADK agent intelligence layer
│   │   │   ├── audit_bridge.py   # Two-pass learning coordinator
│   │   │   ├── explanation.py    # Plain-language risk explainer
│   │   │   ├── knowledge.py      # KnowledgeProvider adapter (delegates to knowledge package)
│   │   │   ├── orchestrator.py   # Full audit orchestrator
│   │   │   ├── remediation.py    # Advisory remediation generator
│   │   │   ├── schemas.py        # Pydantic schemas and rule catalogs
│   │   │   └── teach_auditor.py  # Unfamiliar command interpretation service
│   │   ├── api/                  # Flask REST API blueprint and routes
│   │   │   └── routes.py         # /health, /scan, /scans/<scan_id>
│   │   ├── database/             # SQLite database layer
│   │   │   ├── connection.py     # Connection factory with PRAGMA foreign_keys = ON
│   │   │   ├── repositories.py   # Parameterized CRUD repositories (Scan, Device, RuleResult)
│   │   │   └── schema.py         # DDL schemas and indexes
│   │   ├── models/               # Domain models
│   │   │   ├── device.py         # Device entity
│   │   │   ├── normalized_config.py # Parsed vendor-agnostic configuration model
│   │   │   ├── rule.py           # Compliance rule definition
│   │   │   ├── rule_result.py    # Single rule evaluation result
│   │   │   └── scan.py           # Scan job record
│   │   ├── parsers/              # Configuration parsers
│   │   │   ├── base.py           # BaseParser interface
│   │   │   └── cisco_like.py     # Cisco IOS / IOS-XE deterministic parser
│   │   ├── rules/                # Deterministic compliance engine
│   │   │   ├── checks.py         # NET-001 through NET-010 evaluation logic
│   │   │   ├── definitions.py    # Rule metadata catalog
│   │   │   └── engine.py         # ComplianceEngine orchestrator
│   │   ├── security/             # Sanitization and secret masking
│   │   │   └── sanitization.py   # Regex-based credential redactor
│   │   └── services/             # Core business services
│   │       ├── compliance.py     # Score calculation & summary aggregation
│   │       └── scanner.py        # run_scan() workflow entry point
│   ├── knowledge/                # Persistent Teach-the-Auditor knowledge layer
│   │   ├── fixtures/             # Synthetic JSON fixtures for cross-vendor tests
│   │   ├── models/               # KnowledgeMapping model & ApprovalStatus enum
│   │   ├── services/             # KnowledgeService approval workflow
│   │   ├── storage/              # SQLite database and repository for knowledge mappings
│   │   ├── tests/                # Isolated knowledge layer test suite (44 tests)
│   │   └── validation/           # Command normalization & secret sanitization
│   ├── examples/                 # Executable demos
│   │   ├── phoenix_end_to_end_demo.py # Complete 13-step integration lifecycle demo
│   │   └── teach_auditor_smoke_test.py # Smoke test for ADK agent
│   ├── sample_data/              # Configuration fixtures
│   │   ├── baseline/             # compliant, failing, ambiguous router configs
│   │   ├── edge_cases/           # garbage, malformed, partial configs
│   │   ├── scenarios/            # rule-specific isolation configs & multi-device
│   │   ├── security/             # secret-containing configurations
│   │   └── services/             # insecure services configurations
│   ├── tests/                    # Automated pytest suite (133 tests)
│   ├── .env.example              # Environment configuration example
│   ├── .flake8                   # Flake8 linter config
│   ├── pyrightconfig.json        # Pyright type checker config
│   ├── README.md                 # Backend documentation
│   └── requirements.txt          # Python runtime and test dependencies
├── frontend/                     # Decoupled web client
└── README.md                     # Root project documentation
```

---

## 2. API Endpoints

| Method | Endpoint | Description | Status Codes |
|---|---|---|---|
| `GET` | `/health` | Service operational health check | `200 OK` |
| `POST` | `/scan` | Upload 1+ configs, parse, evaluate NET-001..NET-010 | `201 Created`, `400 Bad Request`, `413 Payload Too Large`, `422 Unprocessable Entity` |
| `GET` | `/scans/<scan_id>` | Retrieve persisted scan results by ID | `200 OK`, `404 Not Found` |

---

## 3. Execution Flow

```text
HTTP Multipart Upload (POST /scan)
        │
        ▼
[Flask Blueprint: upload_and_scan]
        │
        ▼
[File Validation & UTF-8 Decoding] ──(Empty / >10MB / Non-UTF8)──> 400 / 413 / 422 Error
        │
        ▼
[Scanner Service: run_scan()]
        │
        ├─► [CiscoLikeParser.parse()] ──► NormalizedConfig (credentials redacted in evidence)
        │
        ├─► [ComplianceEngine.evaluate()] ──► RuleResult[] (NET-001..NET-010 deterministic verdicts)
        │
        ├─► [Compliance Service: calculate_device_summary() & calculate_scan_summary()]
        │
        └─► [SQLite Repositories: ScanRepository, DeviceRepository, RuleResultRepository]
                │
                ▼
        API Response (JSON 201 Created)
```

---

## 4. Architectural Boundaries and Trust Model

1. **Deterministic Compliance Core (`app/rules/`, `app/parsers/`, `app/services/`)**:
   - The compliance engine evaluates rules purely from `NormalizedConfig`.
   - AI is **never** consulted to decide if a rule passes or fails.
   - Compliance score calculation is purely arithmetic: $\frac{\text{passed}}{\text{passed} + \text{failed}} \times 100\%$.
   - Warnings, errors, and not_applicable results are completely excluded from the denominator.

2. **AI / ADK Agent Intelligence Layer (`app/agents/`)**:
   - `TeachAuditorService`: Synthesizes interpretations for unknown syntax.
   - `FindingExplainer`: Contextualizes deterministic failures for humans.
   - `RemediationService`: Suggests advisory config fixes (`requires_human_approval = True`).
   - Zero execution capabilities (no subprocess, no SSH, no paramiko).
   - If AI is offline, falls back to deterministic local handlers with zero compliance impact.

3. **Knowledge Layer (`knowledge/`)**:
   - Stores learned command interpretations in an isolated database.
   - Enforces approval workflow: only `approved` mappings are ever returned as trusted knowledge.
   - `proposed` or `rejected` mappings return `None` upon lookup.
   - Does NOT make compliance decisions.

---

## 5. Discrepancy Analysis: Documented vs Actual Implementation

| Item | Documented Claim | Actual Implementation Observed | Discrepancy Status |
|---|---|---|---|
| **Backend Location** | Dedicated `backend/` directory | All backend code, tests, configs reside in `backend/` | **MATCH** |
| **Dev2 Package** | `dev 2 part/` mentioned in earlier docs | Successfully promoted to `backend/knowledge/` | **RESOLVED** |
| **Supported Devices** | Cisco IOS (Cisco-like) | `cisco_ios` is actively supported; unsupported types rejected with 400 | **MATCH** |
| **Deterministic Rules** | NET-001 through NET-010 | All 10 rules implemented in `definitions.py` and `checks.py` | **MATCH** |
| **Database Persistence** | SQLite parameterized storage | `scans`, `devices`, `rules`, `rule_results` tables with FK cascade | **MATCH** |
| **AI Authority** | Advisory only | AI has zero influence on deterministic verdicts and zero device execution primitives | **MATCH** |
