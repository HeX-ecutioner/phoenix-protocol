# Phoenix Protocol

> **A safe, evidence-first network configuration compliance scanner for small teams.**

Phoenix Protocol checks exported network-device configuration files against a transparent set of security rules. It shows whether each rule passes, fails, needs manual review, or could not be evaluated.

The project is designed for a hackathon MVP and beginner developers. It is **read-only**: it does not connect to production devices or automatically change configurations.

## Table of contents

- [Problem](#problem)
- [Solution](#solution)
- [How it works](#how-it-works)
- [MVP scope](#mvp-scope)
- [Features](#features)
- [Demo flow](#demo-flow)
- [Technology stack](#technology-stack)
- [Project structure](#project-structure)
- [Getting started](#getting-started)
- [Using the application](#using-the-application)
- [API overview](#api-overview)
- [Security and privacy](#security-and-privacy)
- [Limitations](#limitations)
- [Testing](#testing)
- [Hackathon implementation plan](#hackathon-implementation-plan)
- [Future improvements](#future-improvements)
- [Contributing](#contributing)
- [License](#license)

## Problem

Organizations may manage hundreds or thousands of routers, switches, firewalls, wireless controllers, and virtual network appliances. Each device has security settings that should follow an organizational policy or security standard.

Manual checking requires an administrator to inspect devices individually, compare settings with a checklist, and record the results. This process is slow, inconsistent, and difficult to repeat. Different vendors also use different configuration syntax for similar settings.

Phoenix Protocol focuses on **configuration compliance**. It does not claim to prove that a device is completely secure.

## Solution

Phoenix Protocol lets a user:

1. Upload one or more sanitized configuration files.
2. Select the supported device type.
3. Parse the configuration into security-relevant settings.
4. Evaluate deterministic compliance rules.
5. Review pass, fail, warning, not-applicable, and error results.
6. Inspect evidence and plain-language explanations.
7. Download a CSV or HTML compliance report.

The first version supports one Cisco-like configuration format and approximately 10 rules. This narrow scope makes the project realistic for a short hackathon.

## How it works

```text
Configuration files
        |
        v
File validation
        |
        v
Vendor-specific parser
        |
        v
Normalized configuration data
        |
        v
Deterministic compliance rules
        |
        v
Evidence-based results
        |
        +--> Dashboard
        |
        +--> Device details
        |
        +--> CSV or HTML report
```

The frontend displays results. The backend performs parsing and compliance decisions. The database stores scan metadata and rule results.

## MVP scope

### Included

- Upload at least three text configuration files in one scan.
- Support one vendor or device configuration format.
- Run approximately 10 deterministic security rules.
- Display pass, fail, warning, not-applicable, and error statuses.
- Show configuration evidence or source line references when available.
- Prioritize high-severity failures.
- Display a summary dashboard.
- Display device-level rule results.
- Export CSV or HTML reports.
- Use sanitized or synthetic sample configurations.
- Validate uploaded files safely.
- Test parser and rule behavior.

### Excluded from the MVP

- Automatic changes to live devices.
- Direct SSH, SNMP, or network-device API connections.
- Support for every network vendor.
- Complete vulnerability scanning.
- Full implementation of every security framework.
- Real-time monitoring.
- Enterprise authentication and multi-tenant access control.
- Automatic remediation tickets.
- AI-based compliance decisions.

## Features

### Multi-file upload

Upload several text-based configurations in a single scan. Invalid files should be reported without preventing valid files from being processed.

### Transparent rules

Each rule has a stable identifier, title, severity, description, evaluation logic, evidence, and remediation guidance.

### Evidence-first results

The application shows the configuration line or extracted value used to reach a result whenever safe evidence is available.

### Beginner-friendly explanations

Technical failures are explained in plain language. For example, a Telnet failure explains why a secure administration method should be used instead.

### Prioritized findings

High-severity failures appear first so users can focus on the most important issues.

### Report export

Users can download a report containing scan details, devices, rule results, evidence, explanations, severity, and remediation guidance.

## Initial security rules

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

These rules are demonstration examples. They must be reviewed against the selected vendor’s syntax and the organization’s actual policy before being treated as authoritative compliance checks.

## Demo flow

The recommended demo uses three sanitized files:

1. `compliant_router.txt` contains mostly secure settings.
2. `failing_router.txt` contains obvious high-risk failures such as enabled Telnet or missing logging.
3. `ambiguous_router.txt` contains incomplete settings that produce warnings.

During the demo:

1. Open Phoenix Protocol.
2. Select the supported device type.
3. Upload the three sample files.
4. Click **Run compliance scan**.
5. Show the summary dashboard.
6. Open the failing device.
7. Filter to high-severity failures.
8. Show evidence and remediation guidance.
9. Open the ambiguous device and show a warning.
10. Download the report.

The complete flow should work without changing source code during the presentation.

## Technology stack

| Layer | Technology | Reason |
|---|---|---|
| User interface | HTML, CSS, and JavaScript | Simple for beginners and sufficient for the MVP |
| Backend | Python with Flask | Lightweight and suitable for text processing |
| Parser | Python functions and carefully tested regular expressions | Enough for one controlled vendor format |
| Rule engine | Python functions with structured metadata | Deterministic and easy to test |
| Database | SQLite | No separate database server is required |
| Reports | Python CSV module and HTML templates | Simple and practical exports |
| Testing | Pytest | Clear automated tests |
| Version control | Git and GitHub | Collaboration and rollback |
| Deployment | Local Python server or one Docker container | Simple hackathon deployment |

## Project structure

```text
phoenix_protocol/
├── app.py                  # Starts the Flask application
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
├── .env.example            # Optional environment variable names
├── .gitignore
├── phoenix_protocol/
│   ├── __init__.py
│   ├── routes.py           # Web pages and API endpoints
│   ├── database.py         # SQLite connections and queries
│   ├── models.py           # Scan, device, rule, and result structures
│   ├── validators.py       # Upload validation
│   ├── parsers/
│   │   ├── __init__.py
│   │   └── cisco_like.py   # First supported parser
│   ├── rules/
│   │   ├── __init__.py
│   │   ├── definitions.py  # Rule metadata
│   │   └── checks.py       # Deterministic rule checks
│   ├── services/
│   │   ├── scanner.py      # Coordinates parsing and evaluation
│   │   └── reports.py      # CSV and HTML reports
│   ├── templates/
│   │   ├── base.html
│   │   ├── upload.html
│   │   ├── dashboard.html
│   │   ├── device.html
│   │   └── rules.html
│   └── static/
│       ├── styles.css
│       └── app.js
├── sample_data/
│   ├── compliant_router.txt
│   ├── failing_router.txt
│   └── ambiguous_router.txt
└── tests/
    ├── test_parser.py
    ├── test_rules.py
    └── test_scan_flow.py
```

## Getting started

### Prerequisites

Install the following before starting:

- Python 3.10 or newer.
- Git.
- A code editor such as Visual Studio Code.
- A terminal or command prompt.

### 1. Clone the repository

```bash
git clone <repository-url>
cd phoenix_protocol
```

Replace `<repository-url>` with the URL of the team’s repository.

### 2. Create a virtual environment

A virtual environment keeps this project’s Python packages separate from other projects.

#### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

A minimal `requirements.txt` might contain:

```text
Flask
pytest
python-dotenv
```

### 4. Configure optional environment variables

Copy the example file:

```bash
cp .env.example .env
```

The MVP should not require API keys. Keep secrets out of source control.

### 5. Start the application

```bash
flask --app app run --debug
```

Open the displayed local URL, usually:

```text
http://127.0.0.1:5000
```

For a hosted environment, use the host and port required by that platform and disable debug mode.

## Using the application

1. Open the upload page.
2. Select the supported device type.
3. Choose one or more sanitized configuration files.
4. Click **Run compliance scan**.
5. Review the summary counts.
6. Open a device to inspect rule-level results.
7. Review evidence and remediation guidance.
8. Download a CSV or HTML report.

### Result meanings

| Status | Meaning |
|---|---|
| Pass | Available evidence satisfies the rule |
| Fail | Available evidence violates the rule |
| Warning | The system cannot decide confidently or manual review is needed |
| Not applicable | The rule does not apply to the selected device type |
| Error | Parsing or evaluation failed |

A compliance percentage represents only the tested rules. It is not a complete security score.

## API overview

The backend exposes a small REST API under `/api`.

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Check service availability |
| `GET` | `/api/device-types` | List supported device types |
| `POST` | `/api/scans` | Upload files and run a scan |
| `GET` | `/api/scans/{scan_id}` | Get scan summary |
| `GET` | `/api/scans/{scan_id}/devices` | List devices in a scan |
| `GET` | `/api/scans/{scan_id}/devices/{device_id}` | Get device rule results |
| `GET` | `/api/rules` | List compliance rules |
| `GET` | `/api/rules/{rule_id}` | Get rule details |
| `GET` | `/api/scans/{scan_id}/report.csv` | Download CSV report |
| `GET` | `/api/scans/{scan_id}/report.html` | Download HTML report |

Example upload:

```bash
curl -X POST http://localhost:5000/api/scans \
  -F "device_type=cisco-like-router" \
  -F "files=@sample_data/compliant_router.txt" \
  -F "files=@sample_data/failing_router.txt" \
  -F "files=@sample_data/ambiguous_router.txt"
```

See the complete API specification in [phoenix-protocol-api.md](phoenix-protocol-api.md).

## Database

The MVP uses SQLite. The main tables are:

- `scans`: One row per scan operation.
- `devices`: One row per processed configuration.
- `rules`: The compliance-rule catalog.
- `rule_results`: One row per rule evaluation.

See the complete database design in [phoenix-protocol-database-schema.md](phoenix-protocol-database-schema.md).

## Security and privacy

This prototype should use only fake or sanitized configurations.

- Never upload real passwords, keys, tokens, or production secrets to a public demo.
- Treat every uploaded file as untrusted text.
- Never execute an uploaded file.
- Enforce file size and file-count limits.
- Sanitize filenames.
- Store temporary files outside the public web directory.
- Delete temporary files after processing when practical.
- Do not log complete configuration contents.
- Mask secret-like evidence before displaying it.
- Escape configuration text before inserting it into HTML.
- Do not connect to live network devices in the MVP.
- Do not automatically apply remediation commands.

## Limitations

Phoenix Protocol is a hackathon prototype. It has important limitations:

- The first version supports only one device configuration format.
- Rules are examples and must be validated before operational use.
- A passing result does not prove complete security.
- The scanner checks configuration text, not every vulnerability or runtime condition.
- Ambiguous syntax may require manual review.
- The MVP does not connect to live devices.
- The MVP does not retain a production-grade audit history.
- The MVP is not designed for sensitive production configurations without further security review.

## Testing

Run the automated tests with:

```bash
pytest
```

At minimum, tests should cover:

- Valid and invalid configuration parsing.
- Telnet pass and fail cases.
- Secure administration pass and fail cases.
- Logging pass and warning cases.
- Evidence line extraction.
- Invalid uploads.
- A full scan containing compliant, failing, and ambiguous files.
- Report generation.

The same input, parser version, and rule-set version should produce the same results.

## Hackathon implementation plan

| Phase | Deliverable |
|---|---|
| 1 | Confirm one vendor, define rules, and prepare sample files |
| 2 | Build upload page and file validation |
| 3 | Build the parser and evidence extraction |
| 4 | Implement deterministic rules and tests |
| 5 | Build dashboard and device details |
| 6 | Add report export |
| 7 | Test errors, warnings, and security behavior |
| 8 | Rehearse the demo and document limitations |

Build the scanner and rule correctness before spending time on visual polish.

## Future improvements

After the MVP is stable, the project could add:

- A second vendor parser.
- Automatic device-type detection.
- YAML-based custom rules.
- Mapping to CIS Benchmarks, NIST controls, or internal policies.
- Scan history and trend charts.
- Read-only SSH or API collection.
- Configuration drift alerts.
- User accounts and role-based access.
- Ticketing or SIEM integrations.
- Optional AI summaries of already-determined findings.
- Multilingual explanations.

## Contributing

For a hackathon team:

1. Create a feature branch.
2. Make one focused change.
3. Add or update tests.
4. Run `pytest`.
5. Review the change with another team member.
6. Open a pull request.

Keep parser logic, rule logic, database logic, and presentation logic separate. This makes the code easier for beginners to understand and easier for an AI coding agent to modify safely.

## License

Choose a license before public release. For a hackathon repository, the team may use the MIT License if it wants others to reuse the code. Add the final license text to a `LICENSE` file.

## References

[1]: https://www.nist.gov/cyberframework "NIST Cybersecurity Framework"

[2]: https://www.cisecurity.org/controls "CIS Critical Security Controls"

[3]: https://www.cisecurity.org/benchmark/network-devices "CIS Benchmarks for Network Devices"

[4]: https://flask.palletsprojects.com/ "Flask Documentation"

[5]: https://owasp.org/www-project-api-security/ "OWASP API Security Top 10"
