# Phoenix Protocol Database Schema

**Document status:** Hackathon MVP database design  
**Database:** SQLite  
**Purpose:** Store scan metadata, uploaded-device results, and rule-level compliance findings

## Database design summary

Phoenix Protocol needs to remember what was scanned and what each rule found. The MVP can use four main tables:

```text
scans 1 ──────── many devices
                       |
                       |
                       1
                       |
                       many
                 rule_results

rules 1 ──────── many rule_results
```

The tables are:

1. **`scans`** stores one record for each scan operation.
2. **`devices`** stores each configuration file or device processed during a scan.
3. **`rules`** stores the compliance rules used by the application.
4. **`rule_results`** stores the result of applying one rule to one device.

A fifth table, **`scan_files`**, is optional. It is useful if the team wants to track upload filenames separately from device results. For the simplest MVP, the device record can store the safe display filename and the additional table can be skipped.

## 1. Tables

### Table overview

| Table | Why it exists | One row represents |
|---|---|---|
| `scans` | Groups one scan operation and stores its summary metadata | One user-initiated scan |
| `devices` | Stores the device/configuration files included in a scan | One processed configuration |
| `rules` | Provides a central catalog of compliance checks | One compliance rule |
| `rule_results` | Records the result of one rule for one device | One rule evaluation |
| `scan_files` | Optionally tracks uploaded files | One uploaded file |

## 2. Columns, data types, and required fields

SQLite uses flexible type storage, but the following declared types make the design clear and portable.

### 2.1 `scans` table

The `scans` table is the parent record for one complete scan. A scan may contain several devices.

| Column | SQLite type | Required? | Key | Description |
|---|---|---:|---|---|
| `id` | `TEXT` | Yes | Primary key | Unique scan identifier, preferably a UUID |
| `created_at` | `TEXT` | Yes | — | Scan start or creation time in UTC ISO-8601 format |
| `completed_at` | `TEXT` | No | — | Time when processing finished |
| `device_type` | `TEXT` | Yes | — | Parser/device type selected by the user |
| `status` | `TEXT` | Yes | — | `running`, `completed`, `completed_with_errors`, or `failed` |
| `parser_version` | `TEXT` | Yes | — | Version of the parser used |
| `rule_set_version` | `TEXT` | Yes | — | Version of the rule set used |
| `device_count` | `INTEGER` | Yes | — | Number of device records in the scan |
| `pass_count` | `INTEGER` | Yes | — | Number of passing rule results |
| `fail_count` | `INTEGER` | Yes | — | Number of failing rule results |
| `warning_count` | `INTEGER` | Yes | — | Number of warning results |
| `error_count` | `INTEGER` | Yes | — | Number of error results |
| `compliance_percentage` | `REAL` | No | — | Tested-rule compliance percentage |
| `error_message` | `TEXT` | No | — | Scan-level error, if the entire scan failed |

The count columns are summary values. They make dashboard queries fast. The detailed truth remains in `rule_results`.

### 2.2 `devices` table

The `devices` table represents each configuration processed inside a scan. The MVP may not know the real device name, so `display_name` can initially be a safe filename.

| Column | SQLite type | Required? | Key | Description |
|---|---|---:|---|---|
| `id` | `TEXT` | Yes | Primary key | Unique device-result identifier |
| `scan_id` | `TEXT` | Yes | Foreign key | References `scans.id` |
| `display_name` | `TEXT` | Yes | — | Safe filename or extracted device name |
| `vendor` | `TEXT` | Yes | — | Vendor or parser family, such as `cisco-like` |
| `device_type` | `TEXT` | Yes | — | Device type used for evaluation |
| `parse_status` | `TEXT` | Yes | — | `parsed`, `warning`, or `error` |
| `source_hash` | `TEXT` | No | — | Hash of the source file for duplicate detection |
| `line_count` | `INTEGER` | No | — | Number of lines in the configuration |
| `error_message` | `TEXT` | No | — | Parsing error or warning explanation |
| `created_at` | `TEXT` | Yes | — | Time the device record was created |

Do not store the complete raw configuration in this table for the hackathon MVP. Configuration files may contain secrets and sensitive network information.

### 2.3 `rules` table

The `rules` table is the application’s rule catalog. Storing rule metadata in a table makes the rule library visible and allows results to refer to a stable rule ID.

| Column | SQLite type | Required? | Key | Description |
|---|---|---:|---|---|
| `id` | `TEXT` | Yes | Primary key | Stable identifier such as `NET-001` |
| `title` | `TEXT` | Yes | — | Short rule name |
| `description` | `TEXT` | Yes | — | Plain-language explanation |
| `technical_requirement` | `TEXT` | Yes | — | More precise technical requirement |
| `severity` | `TEXT` | Yes | — | `high`, `medium`, or `low` |
| `device_type` | `TEXT` | Yes | — | Device type to which the rule applies |
| `remediation` | `TEXT` | Yes | — | Suggested next step |
| `is_active` | `INTEGER` | Yes | — | `1` if available for scans, otherwise `0` |
| `rule_version` | `TEXT` | Yes | — | Version of this rule definition |
| `created_at` | `TEXT` | Yes | — | Time the rule was added |
| `updated_at` | `TEXT` | Yes | — | Time the rule metadata was last changed |

The actual Python evaluation function does not need to be stored in SQLite. The application code can map `NET-001` to a tested Python function.

### 2.4 `rule_results` table

The `rule_results` table is the most important detail table. It records what happened when one rule was evaluated against one device.

| Column | SQLite type | Required? | Key | Description |
|---|---|---:|---|---|
| `id` | `TEXT` | Yes | Primary key | Unique result identifier |
| `device_id` | `TEXT` | Yes | Foreign key | References `devices.id` |
| `rule_id` | `TEXT` | Yes | Foreign key | References `rules.id` |
| `status` | `TEXT` | Yes | — | `pass`, `fail`, `warning`, `not_applicable`, or `error` |
| `severity` | `TEXT` | Yes | — | Snapshot of severity at evaluation time |
| `evidence` | `TEXT` | No | — | Masked source line or extracted value |
| `evidence_start_line` | `INTEGER` | No | — | First relevant source line |
| `evidence_end_line` | `INTEGER` | No | — | Last relevant source line |
| `message` | `TEXT` | Yes | — | Result explanation shown to the user |
| `remediation` | `TEXT` | Yes | — | Guidance shown to the user |
| `evaluated_at` | `TEXT` | Yes | — | Evaluation time in UTC |
| `engine_version` | `TEXT` | Yes | — | Version of the compliance engine |
| `error_message` | `TEXT` | No | — | Evaluation error details, if applicable |

The `severity`, `remediation`, and `message` values are stored as a snapshot. This means an old report remains understandable even if the rule definition changes later.

### 2.5 Optional `scan_files` table

Use this table if the team wants separate upload tracking. It is not necessary for the smallest MVP.

| Column | SQLite type | Required? | Key | Description |
|---|---|---:|---|---|
| `id` | `TEXT` | Yes | Primary key | Unique file identifier |
| `scan_id` | `TEXT` | Yes | Foreign key | References `scans.id` |
| `original_filename` | `TEXT` | Yes | — | Original filename for user feedback |
| `safe_filename` | `TEXT` | Yes | — | Sanitized filename used internally |
| `content_type` | `TEXT` | Yes | — | Detected or declared content type |
| `size_bytes` | `INTEGER` | Yes | — | File size |
| `sha256` | `TEXT` | No | — | Content hash |
| `processing_status` | `TEXT` | Yes | — | `accepted`, `processed`, `rejected`, or `error` |
| `error_message` | `TEXT` | No | — | Upload or processing error |
| `created_at` | `TEXT` | Yes | — | Upload time |

The application should not store the file contents in the database. If temporary files are used, they should be stored outside the public web directory and deleted after processing when practical.

## 3. Primary keys

Every table has a primary key:

- `scans.id`
- `devices.id`
- `rules.id`
- `rule_results.id`
- `scan_files.id`, if the optional table is used

The MVP should use UUID strings for scan, device, and result IDs. UUIDs are difficult to guess and work well when records are created by different parts of the application.

Rule IDs are human-readable stable identifiers such as `NET-001`. They are not random because users and reports need to refer to them.

## 4. Foreign keys

The foreign-key relationships are:

| Child column | Parent column | Meaning |
|---|---|---|
| `devices.scan_id` | `scans.id` | Each device belongs to one scan |
| `rule_results.device_id` | `devices.id` | Each result belongs to one processed device |
| `rule_results.rule_id` | `rules.id` | Each result refers to one rule |
| `scan_files.scan_id` | `scans.id` | Each uploaded file belongs to one scan |

SQLite does not always enforce foreign keys unless they are enabled. The application should execute:

```sql
PRAGMA foreign_keys = ON;
```

when opening each database connection.

## 5. Relationships

### Scan to devices

One scan can contain many devices. A device belongs to exactly one scan.

```text
scans 1 ──── many devices
```

### Device to rule results

One device is evaluated against many rules. Each rule evaluation creates one result.

```text
devices 1 ──── many rule_results
```

### Rule to rule results

One rule can be evaluated against many devices and scans.

```text
rules 1 ──── many rule_results
```

### Scan to files

If `scan_files` is used, one scan can contain many uploaded files.

```text
scans 1 ──── many scan_files
```

## 6. Required and optional fields

### Required fields

The following fields are required because the application cannot explain or group a result without them:

- Scan ID, timestamp, device type, status, and version information.
- Device scan ID, display name, vendor, device type, and parse status.
- Rule ID, title, explanation, severity, applicable device type, and remediation.
- Rule-result device ID, rule ID, status, severity, message, remediation, evaluation time, and engine version.

### Optional fields

The following fields may be empty during the MVP:

- Scan completion time.
- Scan-level error message.
- Compliance percentage.
- Source hash.
- Line count.
- Parse error message.
- Evidence text and line range, when no safe evidence is available.
- Evaluation error message.
- File hash, if the optional file table is used.

A warning should be stored as a result, not represented by a missing value. Missing evidence and a warning status are different concepts.

## 7. Useful indexes

Indexes help the application find records without scanning every row.

```sql
CREATE INDEX idx_devices_scan_id
    ON devices(scan_id);

CREATE INDEX idx_rule_results_device_id
    ON rule_results(device_id);

CREATE INDEX idx_rule_results_rule_id
    ON rule_results(rule_id);

CREATE INDEX idx_rule_results_status
    ON rule_results(status);

CREATE INDEX idx_rule_results_severity_status
    ON rule_results(severity, status);

CREATE INDEX idx_scans_created_at
    ON scans(created_at);
```

A useful uniqueness constraint prevents duplicate evaluation of the same rule for the same device within one scan:

```sql
CREATE UNIQUE INDEX idx_one_result_per_device_rule
    ON rule_results(device_id, rule_id);
```

If the application later supports multiple evaluations of the same rule in one scan, this constraint should be changed. The MVP should keep one result per device and rule.

## 8. Example records

The following records represent three demo devices: one mostly compliant device, one failing device, and one ambiguous device.

### Example `scans` record

| id | created_at | device_type | status | device_count | pass_count | fail_count | warning_count | error_count | compliance_percentage |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| `scan-001` | `2026-09-11T09:00:00Z` | `cisco-like-router` | `completed` | 3 | 21 | 6 | 3 | 0 | 77.78 |

### Example `devices` records

| id | scan_id | display_name | vendor | device_type | parse_status |
|---|---|---|---|---|---|
| `dev-001` | `scan-001` | `compliant-router.txt` | `cisco-like` | `cisco-like-router` | `parsed` |
| `dev-002` | `scan-001` | `failing-router.txt` | `cisco-like` | `cisco-like-router` | `parsed` |
| `dev-003` | `scan-001` | `ambiguous-router.txt` | `cisco-like` | `cisco-like-router` | `warning` |

### Example `rules` records

| id | title | severity | device_type | is_active |
|---|---|---|---|---:|
| `NET-001` | Telnet is disabled | `high` | `cisco-like-router` | 1 |
| `NET-002` | Secure administration is enabled | `high` | `cisco-like-router` | 1 |
| `NET-005` | System logging is enabled | `high` | `cisco-like-router` | 1 |

### Example `rule_results` records

| id | device_id | rule_id | status | severity | evidence | message |
|---|---|---|---|---|---|---|
| `res-001` | `dev-001` | `NET-001` | `pass` | `high` | `line 24: no transport input telnet` | `Telnet does not appear to be enabled.` |
| `res-002` | `dev-002` | `NET-001` | `fail` | `high` | `line 24: transport input telnet` | `Telnet appears to be enabled.` |
| `res-003` | `dev-003` | `NET-005` | `warning` | `high` | `No logging configuration found` | `The system could not confidently determine whether logging is enabled.` |

Evidence containing secrets should be masked before being saved or displayed.

## 9. SQL schema

The following SQL creates the recommended MVP schema. It uses SQLite syntax.

```sql
PRAGMA foreign_keys = ON;

CREATE TABLE scans (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    device_type TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('running', 'completed', 'completed_with_errors', 'failed')
    ),
    parser_version TEXT NOT NULL,
    rule_set_version TEXT NOT NULL,
    device_count INTEGER NOT NULL DEFAULT 0 CHECK (device_count >= 0),
    pass_count INTEGER NOT NULL DEFAULT 0 CHECK (pass_count >= 0),
    fail_count INTEGER NOT NULL DEFAULT 0 CHECK (fail_count >= 0),
    warning_count INTEGER NOT NULL DEFAULT 0 CHECK (warning_count >= 0),
    error_count INTEGER NOT NULL DEFAULT 0 CHECK (error_count >= 0),
    compliance_percentage REAL CHECK (
        compliance_percentage IS NULL
        OR (compliance_percentage >= 0 AND compliance_percentage <= 100)
    ),
    error_message TEXT
);

CREATE TABLE devices (
    id TEXT PRIMARY KEY,
    scan_id TEXT NOT NULL,
    display_name TEXT NOT NULL,
    vendor TEXT NOT NULL,
    device_type TEXT NOT NULL,
    parse_status TEXT NOT NULL CHECK (
        parse_status IN ('parsed', 'warning', 'error')
    ),
    source_hash TEXT,
    line_count INTEGER CHECK (line_count IS NULL OR line_count >= 0),
    error_message TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE
);

CREATE TABLE rules (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    technical_requirement TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('high', 'medium', 'low')),
    device_type TEXT NOT NULL,
    remediation TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    rule_version TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE rule_results (
    id TEXT PRIMARY KEY,
    device_id TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('pass', 'fail', 'warning', 'not_applicable', 'error')
    ),
    severity TEXT NOT NULL CHECK (severity IN ('high', 'medium', 'low')),
    evidence TEXT,
    evidence_start_line INTEGER CHECK (
        evidence_start_line IS NULL OR evidence_start_line > 0
    ),
    evidence_end_line INTEGER CHECK (
        evidence_end_line IS NULL OR evidence_end_line > 0
    ),
    message TEXT NOT NULL,
    remediation TEXT NOT NULL,
    evaluated_at TEXT NOT NULL,
    engine_version TEXT NOT NULL,
    error_message TEXT,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    FOREIGN KEY (rule_id) REFERENCES rules(id) ON DELETE RESTRICT,
    UNIQUE (device_id, rule_id)
);

CREATE TABLE scan_files (
    id TEXT PRIMARY KEY,
    scan_id TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    safe_filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL CHECK (size_bytes >= 0),
    sha256 TEXT,
    processing_status TEXT NOT NULL CHECK (
        processing_status IN ('accepted', 'processed', 'rejected', 'error')
    ),
    error_message TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE
);

CREATE INDEX idx_devices_scan_id
    ON devices(scan_id);

CREATE INDEX idx_rule_results_device_id
    ON rule_results(device_id);

CREATE INDEX idx_rule_results_rule_id
    ON rule_results(rule_id);

CREATE INDEX idx_rule_results_status
    ON rule_results(status);

CREATE INDEX idx_rule_results_severity_status
    ON rule_results(severity, status);

CREATE INDEX idx_scans_created_at
    ON scans(created_at);

CREATE INDEX idx_scan_files_scan_id
    ON scan_files(scan_id);
```

## 10. Example inserts

The following SQL adds a small demo dataset.

```sql
INSERT INTO scans (
    id,
    created_at,
    completed_at,
    device_type,
    status,
    parser_version,
    rule_set_version,
    device_count,
    pass_count,
    fail_count,
    warning_count,
    error_count,
    compliance_percentage
) VALUES (
    'scan-001',
    '2026-09-11T09:00:00Z',
    '2026-09-11T09:00:03Z',
    'cisco-like-router',
    'completed',
    '1.0.0',
    '1.0.0',
    3,
    21,
    6,
    3,
    0,
    77.78
);

INSERT INTO devices (
    id, scan_id, display_name, vendor, device_type,
    parse_status, line_count, created_at
) VALUES
(
    'dev-001', 'scan-001', 'compliant-router.txt',
    'cisco-like', 'cisco-like-router', 'parsed', 120,
    '2026-09-11T09:00:01Z'
),
(
    'dev-002', 'scan-001', 'failing-router.txt',
    'cisco-like', 'cisco-like-router', 'parsed', 98,
    '2026-09-11T09:00:01Z'
),
(
    'dev-003', 'scan-001', 'ambiguous-router.txt',
    'cisco-like', 'cisco-like-router', 'warning', 75,
    '2026-09-11T09:00:02Z'
);

INSERT INTO rules (
    id, title, description, technical_requirement, severity,
    device_type, remediation, is_active, rule_version,
    created_at, updated_at
) VALUES
(
    'NET-001',
    'Telnet is disabled',
    'Telnet is an insecure administration method.',
    'No Telnet administration input should be enabled.',
    'high',
    'cisco-like-router',
    'Disable Telnet after confirming that secure administration is available.',
    1,
    '1.0.0',
    '2026-09-10T12:00:00Z',
    '2026-09-10T12:00:00Z'
),
(
    'NET-002',
    'Secure administration is enabled',
    'Administrative access should use a secure protocol.',
    'SSH or an approved secure administration method should be configured.',
    'high',
    'cisco-like-router',
    'Configure an approved secure administration method and test it before disabling alternatives.',
    1,
    '1.0.0',
    '2026-09-10T12:00:00Z',
    '2026-09-10T12:00:00Z'
),
(
    'NET-005',
    'System logging is enabled',
    'Logging helps administrators investigate events and incidents.',
    'An approved system logging destination should be configured.',
    'high',
    'cisco-like-router',
    'Configure an approved logging destination and verify that events are received.',
    1,
    '1.0.0',
    '2026-09-10T12:00:00Z',
    '2026-09-10T12:00:00Z'
);

INSERT INTO rule_results (
    id, device_id, rule_id, status, severity, evidence,
    evidence_start_line, evidence_end_line, message, remediation,
    evaluated_at, engine_version
) VALUES
(
    'res-001', 'dev-001', 'NET-001', 'pass', 'high',
    'line 24: no transport input telnet', 24, 24,
    'Telnet does not appear to be enabled.',
    'Continue using an approved secure administration method.',
    '2026-09-11T09:00:02Z', '1.0.0'
),
(
    'res-002', 'dev-002', 'NET-001', 'fail', 'high',
    'line 24: transport input telnet', 24, 24,
    'Telnet appears to be enabled.',
    'Disable Telnet after confirming that secure administration is available.',
    '2026-09-11T09:00:02Z', '1.0.0'
),
(
    'res-003', 'dev-003', 'NET-005', 'warning', 'high',
    'No logging configuration found', NULL, NULL,
    'The system could not confidently determine whether logging is enabled.',
    'Review the device configuration manually and confirm the approved logging destination.',
    '2026-09-11T09:00:02Z', '1.0.0'
);
```

## 11. Common queries for the application

### Get a scan summary

```sql
SELECT
    id,
    created_at,
    completed_at,
    device_type,
    status,
    device_count,
    pass_count,
    fail_count,
    warning_count,
    error_count,
    compliance_percentage
FROM scans
WHERE id = ?;
```

### Get devices in a scan

```sql
SELECT
    id,
    display_name,
    vendor,
    device_type,
    parse_status,
    error_message
FROM devices
WHERE scan_id = ?
ORDER BY display_name;
```

### Get high-severity failures

```sql
SELECT
    d.display_name,
    rr.rule_id,
    rr.status,
    rr.severity,
    rr.evidence,
    rr.message,
    rr.remediation
FROM rule_results AS rr
JOIN devices AS d ON d.id = rr.device_id
WHERE d.scan_id = ?
  AND rr.severity = 'high'
  AND rr.status = 'fail'
ORDER BY d.display_name, rr.rule_id;
```

### Get all results for a device

```sql
SELECT
    rr.rule_id,
    r.title,
    rr.status,
    rr.severity,
    rr.evidence,
    rr.message,
    rr.remediation
FROM rule_results AS rr
JOIN rules AS r ON r.id = rr.rule_id
WHERE rr.device_id = ?
ORDER BY
    CASE rr.severity
        WHEN 'high' THEN 1
        WHEN 'medium' THEN 2
        WHEN 'low' THEN 3
    END,
    rr.rule_id;
```

## 12. Data-retention recommendation

For the hackathon MVP, store scan metadata and results in SQLite, but do not permanently store raw configuration files. Temporary uploaded files should be deleted after parsing and evaluation when possible.

If the team needs to demonstrate scan history, retain only sanitized demo results. A future production version would need an explicit retention policy, encryption, access control, deletion workflows, and audit logging.

## 13. Implementation guidance for beginners

The database should not contain the entire application’s logic. The application should follow this simple division:

- **Parser code** reads configuration text.
- **Rule code** decides pass, fail, warning, or error.
- **Database code** stores the scan and results.
- **Frontend code** displays the stored results.

The easiest implementation order is:

1. Create the four required tables.
2. Insert the fixed rule catalog when the application starts.
3. Create a scan record when the user uploads files.
4. Create one device record per valid file.
5. Create one rule-result record for each device and rule.
6. Update the scan summary counts after evaluation.
7. Query the results for the dashboard and report.

## Final recommendation

Use `scans`, `devices`, `rules`, and `rule_results` as the required MVP tables. Add `scan_files` only if separate upload tracking is useful. Use UUID-style text IDs, UTC timestamps, foreign keys, status constraints, and a unique `(device_id, rule_id)` constraint. Store evidence snippets carefully and never treat the database as a reason to retain complete sensitive configurations.

This schema is intentionally small enough for a beginner team to implement during a hackathon while preserving the relationships needed for dashboards, device details, evidence review, and report export.

## References

[1]: https://www.sqlite.org/foreignkeys.html "SQLite Foreign Key Support"

[2]: https://www.sqlite.org/datatype3.html "SQLite Datatypes"

[3]: https://www.sqlite.org/lang_createtable.html "SQLite CREATE TABLE Documentation"

[4]: https://www.sqlite.org/lang_createindex.html "SQLite CREATE INDEX Documentation"

[5]: https://owasp.org/www-project-top-ten/ "OWASP Top 10 Web Application Security Risks"
