# Phoenix Protocol Backend Analysis Track Implementation

## 1. Backend Analysis Architecture Overview
The backend analysis track is built using Python and FastAPI, following a clean architecture pattern. It processes uploaded generic key-value configuration files, normalizes them, evaluates deterministic compliance rules, and persists the outcomes to a local SQLite database. The architecture separates the `parser`, `rules` evaluator, `repository` (persistence layer), and the core orchestrator `service` (`run_scan`). This ensures that the FastAPI application (API boundary) does not calculate compliance metrics directly.

## 2. Data Contract
The main data contract is the `ScanResult` object, returned from both the API (`POST /scan` and `GET /scans/{scan_id}`) and the underlying service.
- **SourceInfo**: Contains file metadata and SHA-256 hash.
- **ParserInfo**: Describes the parser ID and version.
- **ScanSummary**: Aggregated counts of rule statuses and `compliance_percent`.
- **RuleResult**: Detailed outcomes per rule, containing status, evidence, and diagnostics.
- **Evidence**: Shows the parsed setting value vs. the expected value with source line references. Safe display fields (`safe_to_display`) protect sensitive data.
- **Diagnostic**: Structured parser warnings/errors.

## 3. Parser-Supported Format
A `GenericKeyValueParser` was built to parse generic key-value device configurations.
**Supported Format:** 
Lines formatted as `key = value`, `key : value`, or `key value`.
Blank lines and lines starting with `#` are ignored.

**Canonical Settings Supported:**
- `authentication.mfa_enabled` (boolean)
- `authentication.password_min_length` (integer)
- `authentication.password_complexity_enabled` (boolean)
- `authentication.lockout_threshold` (integer)
- `access.default_admin_disabled` (boolean)
- `network.ssh.enabled` (boolean)
- `network.insecure_management_port.enabled` (boolean)
- `logging.audit.enabled` (boolean)
- `logging.remote_logging.enabled` (boolean)
- `time.ntp.enabled` (boolean)
- `time.ntp.servers` (list/string)

## 4. Rule Catalog and Status Semantics
**Rules Implemented:**
- `AUTH-MFA-001`: Multi-factor authentication enabled
- `AUTH-PWD-001`: Minimum password length meets policy (>= 12)
- `AUTH-PWD-002`: Password complexity enabled
- `ACCESS-ADM-001`: Default administrative account disabled
- `NET-SSH-001`: Secure remote administration enabled
- `NET-PORT-001`: Insecure management port disabled
- `LOG-AUD-001`: Audit logging enabled
- `TIME-NTP-001`: Trusted time synchronization configured

**Status Semantics (Frontend Handoff Note):**
The frontend MUST NOT recalculate compliance. The UI should map exactly to these statuses:
- `compliant`: The setting is present and satisfies the rule.
- `failing`: The setting is present but violates the rule.
- `ambiguous`: Information is missing, invalid, or conflicting.
- `not_applicable`: Does not apply.
- `error`: Internal engine error.

## 5. SQLite Schema and Repository Usage
**Tables:**
- `scans`: Tracks global scan metrics and metadata.
- `normalized_settings`: Parsed configuration properties.
- `rule_results`: The outcome of the evaluated rules.
- `evidence`: Specific values used during rule evaluation.
- `diagnostics`: Parser warnings and errors.

The `ScanRepository` handles transactional saves in the `run_scan` orchestrator, safely rolling back during unrecoverable parsing errors.

## 6. Summary Calculation Explanation
The API and frontend must not recalculate these values.
`tested_rules = compliant + failing + ambiguous`
`compliance_percent = (compliant / tested_rules) * 100` if `tested_rules > 0`, else `null`.

## 7. Example Responses
**Compliant (excerpt):**
```json
{
  "scan_id": "scan_123",
  "status": "completed",
  "summary": {
    "total_rules": 8, "tested_rules": 8, "compliant": 8, "failing": 0, "ambiguous": 0, "compliance_percent": 100.0
  }
}
```

**Ambiguous:**
Missing settings trigger `ambiguous` with missing expected evidence records.
```json
{
  "scan_id": "scan_456",
  "status": "completed",
  "summary": {
    "compliant": 0, "failing": 0, "ambiguous": 8, "compliance_percent": 0.0
  }
}
```

## 8. Known Limitations and Excluded Scope
- Multi-file or distributed scanning is not supported.
- Postgres or advanced databases are not implemented.
- Automatic AI compliance validation is strictly avoided for determinism.
- Passwords and secrets are redacted from the response with `safe_to_display = false`.

## 9. Test Results & Failure Log
No endpoint failures remain. All tests are passing.

## 10. Run Instructions
```bash
# Setup Virtual Environment
python -m venv venv
source venv/Scripts/activate # On Windows: .\venv\Scripts\Activate.ps1
pip install fastapi uvicorn pytest black flake8 mypy httpx

# Run tests
pytest -v

# Start Server
uvicorn app.main:app --reload
```
