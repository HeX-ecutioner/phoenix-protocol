# Phoenix Protocol — Backend Track 2: Processing, Database, and Compliance Engine

## Role

**Owner:** Backend developer 2  
**Main responsibility:** Build the configuration parser, deterministic compliance rules, SQLite data layer, scan-processing service, and processing tests.

This track owns the application’s security-analysis logic. It should not own Flask route design or frontend code. Backend Track 1 exposes your services through the API.

## Main workflow owned by this track

```text
Validated text file
    ↓
Vendor parser
    ↓
Normalized configuration
    ↓
Deterministic rule engine
    ↓
Rule results
    ↓
SQLite persistence
    ↓
Scan summary
```

## Recommended technology

- Python 3.10 or newer.
- Python functions and carefully tested regular expressions.
- SQLite.
- Python `sqlite3` module or a very small database helper.
- Pytest.
- Git and GitHub.

Do not add a large parsing framework or a separate database server for the MVP.

## Responsibilities

### 1. Vendor parser

Implement one parser for the selected Cisco-like configuration format.

The parser should:

- Read configuration text line by line.
- Extract security-relevant settings.
- Return normalized fields.
- Preserve source line numbers.
- Return safe evidence snippets.
- Produce warnings for missing or ambiguous settings.
- Return controlled errors instead of crashing the complete scan.

Example normalized output:

```python
{
    "device_name": "edge-router-01",
    "vendor": "cisco-like",
    "device_type": "cisco-like-router",
    "secure_admin_enabled": True,
    "telnet_enabled": False,
    "logging_enabled": True,
    "time_sync_configured": False,
    "admin_access_list_present": True,
    "password_protection_enabled": True,
    "source_lines": {
        "secure_admin_enabled": [12, 13],
        "logging_enabled": [48]
    }
}
```

Do not store the complete raw configuration in the database. Preserve only the evidence needed to explain results, and mask secrets.

### 2. Deterministic rule engine

Build rule checks that accept normalized configuration data and return structured results.

Every result must include:

```python
{
    "status": "fail",
    "severity": "high",
    "evidence": "line 42: transport input telnet",
    "message": "Telnet appears to be enabled.",
    "remediation": "Disable Telnet after confirming secure administration is available."
}
```

Supported statuses:

- `pass`
- `fail`
- `warning`
- `not_applicable`
- `error`

The rule engine must be deterministic. Do not call an AI model for pass/fail decisions.

### 3. Initial rules

Implement approximately 10 rules:

| Rule ID | Check | Severity |
|---|---|---|
| NET-001 | Telnet is disabled | High |
| NET-002 | Secure administration such as SSH is enabled | High |
| NET-003 | Weak or reversible password storage is not used | High |
| NET-004 | Login-failure protection is configured | Medium |
| NET-005 | System logging is enabled | High |
| NET-006 | A trusted time source is configured | Medium |
| NET-007 | An approved administrative access list exists | High |
| NET-008 | Unused insecure services are disabled | Medium |
| NET-009 | Device identification or ownership metadata is present | Low |
| NET-010 | Obvious plaintext secret patterns are absent | High |

Each rule should have metadata:

- Rule ID.
- Title.
- Plain-language description.
- Technical requirement.
- Device type.
- Severity.
- Evaluation function.
- Evidence behavior.
- Remediation guidance.
- Rule version.

These rules are prototype examples and should be validated against the chosen vendor syntax and policy.

### 4. SQLite data layer

Use these tables:

- `scans`.
- `devices`.
- `rules`.
- `rule_results`.

An optional `scan_files` table can track uploads separately, but it is not required for the smallest MVP.

Required relationships:

```text
scans 1 ──── many devices

devices 1 ──── many rule_results

rules 1 ──── many rule_results
```

Enable foreign keys:

```sql
PRAGMA foreign_keys = ON;
```

Use UUID-style text IDs for scans, devices, and results. Use stable human-readable IDs such as `NET-001` for rules.

### 5. Scan-processing service

Create a service that coordinates the complete analysis. A possible interface is:

```python
scan_result = run_scan(
    scan_id=scan_id,
    device_type=device_type,
    uploaded_files=validated_files
)
```

The service should:

1. Create or update the scan record.
2. Process each accepted file.
3. Create one device record per file.
4. Parse each configuration.
5. Record parse warnings or errors.
6. Evaluate all applicable rules.
7. Create rule-result records.
8. Aggregate counts.
9. Calculate tested-rule compliance.
10. Update scan status.
11. Return a structured result for the API layer.

One invalid file should not prevent valid files from being processed when safe.

### 6. Summary calculations

Calculate:

- Device count.
- Total rules evaluated.
- Pass count.
- Fail count.
- Warning count.
- Not-applicable count.
- Error count.
- High-severity failure count.
- Tested-rule compliance percentage.

Use:

```text
passing applicable rules / (passing + failing applicable rules) * 100
```

Warnings and errors must remain visible and separate. Never silently turn warnings into passes.

## Suggested files owned by this track

```text
phoenix_protocol/
├── database.py
├── models.py
├── parsers/
│   ├── __init__.py
│   └── cisco_like.py
├── rules/
│   ├── __init__.py
│   ├── definitions.py
│   └── checks.py
└── services/
    └── scanner.py

tests/
├── test_parser.py
├── test_rules.py
├── test_database.py
└── test_scanner_service.py
```

Agree on shared-file ownership before editing files used by Backend Track 1.

## Database implementation requirements

### `scans`

Store:

- ID.
- Created and completed timestamps.
- Device type.
- Status.
- Parser version.
- Rule-set version.
- Summary counts.
- Tested-rule compliance percentage.

### `devices`

Store:

- ID.
- Scan ID.
- Safe display name.
- Vendor.
- Device type.
- Parse status.
- Line count if available.
- Safe error message if needed.

### `rules`

Store:

- Stable rule ID.
- Title.
- Description.
- Technical requirement.
- Severity.
- Device type.
- Remediation.
- Active flag.
- Rule version.

### `rule_results`

Store:

- ID.
- Device ID.
- Rule ID.
- Status.
- Severity snapshot.
- Evidence.
- Evidence line range.
- Message.
- Remediation snapshot.
- Evaluation timestamp.
- Engine version.
- Error message if needed.

Create a unique constraint for one result per device and rule within a scan design.

## Processing tests

Write unit tests for:

- Secure administration detection.
- Telnet enabled and disabled.
- Logging enabled, missing, and ambiguous.
- Time synchronization configured and missing.
- Access-list detection.
- Password-protection detection.
- Plaintext secret masking.
- Missing settings.
- Contradictory settings.
- All result statuses.
- Rule severity and metadata.

Write service tests for:

- One compliant file.
- One failing file.
- One ambiguous file.
- Three files in one scan.
- One invalid file with valid files.
- Summary count accuracy.
- Repeatability for the same input.
- Database persistence and retrieval.
- Foreign-key behavior.

## Security responsibilities

- Treat configuration input as untrusted text.
- Never execute configuration commands.
- Do not retain complete raw files by default.
- Mask passwords, keys, tokens, and secret-like values.
- Avoid logging complete configurations.
- Use parameterized SQL.
- Enable foreign-key enforcement.
- Use controlled parser errors.
- Do not require production credentials.
- Do not connect to live devices.

## Coordination with Backend Track 1

Provide Track 1:

- `run_scan` function signature.
- Scan result object structure.
- Database query functions.
- Rule metadata format.
- Parser error and warning format.
- Expected scan summary fields.

Request from Track 1:

- Validated upload object format.
- Scan ID generation behavior.
- API response requirements.
- Report data requirements.
- Endpoint integration test failures.

The two backend tracks should agree on data structures before implementation begins.

## Coordination with the frontend developer

Provide:

- Example scan results.
- Expected rule status values.
- Evidence format.
- Meaning of warnings.
- Summary calculation explanation.
- Example records for compliant, failing, and ambiguous devices.

The frontend should display your results but should not recreate your calculations.

## Acceptance criteria

This track is complete when:

- The parser extracts normalized settings from the selected format.
- At least eight rules produce meaningful results.
- All five result statuses are supported.
- Evidence and line references are retained where safe.
- Three sample files produce expected outcomes.
- Scan results are stored in SQLite.
- Summary counts are correct.
- Tested-rule compliance is calculated and labeled properly.
- Processing tests pass.
- The service can be called by the API track without knowing parser internals.

## What not to build

Do not build:

- A second vendor parser before the first is reliable.
- Live SSH, SNMP, or device API collection.
- Automatic remediation.
- AI-based compliance decisions.
- A custom rule-authoring interface.
- PostgreSQL or a separate database server.
- Background processing.
- Distributed scanning.

## Final responsibility statement

You own the correctness of the analysis. The API may receive requests and the frontend may display results, but your parser, rules, database records, and summary calculations determine whether Phoenix Protocol is trustworthy.
