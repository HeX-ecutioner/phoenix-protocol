# Phoenix Protocol — Sample Data & QA Fixture Suite

This directory contains the comprehensive, synthetic, safe network-device configuration fixture suite for **Phoenix Protocol**.

All configurations are strictly synthetic test artifacts.
- **No real credentials, private keys, certificates, or proprietary hashes.**
- **No real organizational IP addresses**; all network addresses use documentation and benchmark ranges defined by RFC 5737 (`192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24`).
- **No external network calls or active device dependencies.**

---

## Directory Organization

```
sample_data/
├── README.md
├── compliant_router.txt              # Canonical 100% compliant baseline (root preserved for test compatibility)
├── failing_router.txt                # Canonical 0% failing baseline (root preserved for test compatibility)
├── ambiguous_router.txt              # Canonical ambiguous baseline (root preserved for test compatibility)
├── baseline/                         # Categorized copies of baseline profiles
│   ├── compliant_router.txt
│   ├── failing_router.txt
│   └── ambiguous_router.txt
├── edge_cases/                       # Parser boundary and defensive evaluation fixtures
│   ├── empty.txt
│   ├── garbage.txt
│   ├── partial_config.txt
│   ├── malformed_banner.txt
│   ├── no_banner.txt
│   ├── multiple_vty_blocks.txt
│   ├── partial_vty_failure.txt
│   ├── ambiguous_transport.txt
│   ├── ntp_peer_only.txt
│   └── local_logging_only.txt
├── security/                         # Credential and sensitive secret sanitization fixtures
│   ├── plaintext_credentials.txt
│   ├── type7_credentials.txt
│   ├── tacacs_radius_secrets.txt
│   └── mixed_secrets.txt
├── services/                         # Service enablement / disabling verification
│   ├── insecure_services_enabled.txt
│   └── insecure_services_disabled.txt
└── scenarios/                        # Rule-specific isolation, positive controls, and demo flows
    ├── net001_telnet.txt
    ├── net002_no_ssh.txt
    ├── net003_weak_credentials.txt
    ├── net004_no_login_protection.txt
    ├── net005_no_logging.txt
    ├── net006_no_ntp.txt
    ├── net007_no_access_class.txt
    ├── net008_insecure_services.txt
    ├── net009_no_banner.txt
    ├── net010_plaintext_secret.txt
    ├── all_security_controls.txt
    ├── minimal_secure_router.txt
    ├── remediation_demo.txt
    ├── multi_device_secondary.txt
    └── executive_demo.txt
```

---

## Fixture Catalog & Specification

### 1. Baseline Profiles

#### `baseline/compliant_router.txt` (and `sample_data/compliant_router.txt`)
- **Purpose**: Canonical positive control representing an enterprise core router satisfying all 10 baseline security controls.
- **Expected Parser Behavior**: Parses successfully, extracts hostname `CORE-RTR-01`, identifies SSH v2, login failure rate-limiting, syslog host, NTP server, dual VTY blocks (0-4 and 5-15) with ACLs, and sanitizes robust scrypt credentials.
- **Relevant Rules**: NET-001 through NET-010.
- **Expected Outcome**: 10/10 PASS (100.0% compliance).
- **Intended Usage**: Automated regression tests (`test_rules.py`, `test_scanner_service.py`, `test_api.py`) and manual happy-path verification.

#### `baseline/failing_router.txt` (and `sample_data/failing_router.txt`)
- **Purpose**: Canonical negative control representing a misconfigured legacy router violating all 10 baseline security controls.
- **Expected Parser Behavior**: Parses successfully, extracts hostname `DEFAULT-RTR`, flags plaintext/Type 7 credentials, enabled Telnet on VTY, missing SSH v2, missing login rate-limiting, missing syslog, and enabled HTTP/small servers.
- **Relevant Rules**: NET-001 through NET-010.
- **Expected Outcome**: 0/10 PASS, 10/10 FAIL (0.0% compliance).
- **Intended Usage**: Automated regression tests and manual failure-state verification.

#### `baseline/ambiguous_router.txt` (and `sample_data/ambiguous_router.txt`)
- **Purpose**: Demonstrates defensive parser and rule behavior when encountering incomplete sections, ambiguous transports, missing hostname, and local-only logging.
- **Expected Parser Behavior**: Preserves parser warnings for missing hostname, ambiguous transport `transport input all`, local buffer without remote host, and unauthoritative NTP peer.
- **Relevant Rules**: NET-001 (FAIL), NET-002 (FAIL), NET-003 (FAIL), NET-004 (FAIL), NET-005 (WARNING), NET-006 (WARNING), NET-007 (FAIL), NET-008 (WARNING), NET-009 (WARNING), NET-010 (PASS).
- **Expected Outcome**: 1 PASS, 5 FAIL, 4 WARNING (16.7% compliance).
- **Intended Usage**: Automated tests and manual warning inspection.

---

### 2. Edge Cases

#### `edge_cases/empty.txt`
- **Purpose**: Verifies parser and scanner resilience against zero-byte empty uploads.
- **Expected Parser Behavior**: Flags error `"Configuration input is empty"` without raising unhandled exceptions.
- **Relevant Rules**: Scanner and API upload validation.
- **Expected Outcome**: Scanner marks device `parse_status: failed`, 10 error findings, 0.0% compliance. HTTP POST `/scan` rejects with 400 Bad Request.
- **Intended Usage**: Automated edge-case tests and API error-handling validation.

#### `edge_cases/garbage.txt`
- **Purpose**: Evaluates system behavior when arbitrary, non-network text is uploaded.
- **Expected Parser Behavior**: Does not crash; records warning `"Missing hostname statement in configuration"`; does not match any valid Cisco security directives.
- **Relevant Rules**: Scanner lifecycle, NET-001 through NET-010.
- **Expected Outcome**: Scan completes safely; device marked `success`; 1 PASS (NET-010 passes due to no plaintext credentials found), 5 FAIL (SSH, passwords, login protection, logging, NTP absent), 4 WARNING (VTY, services, banner absent) (16.7% compliance).
- **Intended Usage**: Manual upload testing and automated crash-resilience tests.

#### `edge_cases/partial_config.txt`
- **Purpose**: Distinguishes valid but fragmentary Cisco configuration lines from complete security baselines.
- **Expected Parser Behavior**: Extracts hostname `FRAGMENT-RTR-01` and interface statements; records no parser crash.
- **Relevant Rules**: NET-001 through NET-010.
- **Expected Outcome**: 1 PASS (NET-010), 6 FAIL, 3 WARNING (14.3% compliance).
- **Intended Usage**: Manual testing of partial config ingest and diagnostic reporting.

#### `edge_cases/malformed_banner.txt`
- **Purpose**: Tests parser defensive handling of an unclosed banner delimiter reached at EOF.
- **Expected Parser Behavior**: Detects unclosed multi-line banner motd; records parser error `"Unclosed banner motd delimiter starting at line 4"` without raising an uncaught exception.
- **Relevant Rules**: Parser resilience, NET-009.
- **Expected Outcome**: 3 PASS, 6 FAIL, 1 WARNING (33.3% compliance).
- **Intended Usage**: Automated parser boundary tests and manual QA.

#### `edge_cases/no_banner.txt`
- **Purpose**: Tests a valid Cisco router configuration with hostname but omitting legal warning banners.
- **Expected Parser Behavior**: Extracts hostname `NO-BANNER-RTR-01` and all secure settings, noting banner motd/login are absent.
- **Relevant Rules**: NET-009.
- **Expected Outcome**: 9 PASS, 1 FAIL (NET-009 fails with message noting banner absence) (90.0% compliance).
- **Intended Usage**: Automated and manual verification of NET-009 banner enforcement.

#### `edge_cases/multiple_vty_blocks.txt`
- **Purpose**: Verifies that Phoenix parses and maintains scoped, separate VTY ranges (`0 4` and `5 15`) rather than flattening them.
- **Expected Parser Behavior**: Both `vty 0 4` and `vty 5 15` are extracted into distinct management blocks, each retaining its own access-class, timeout, and transport settings.
- **Relevant Rules**: NET-001, NET-007.
- **Expected Outcome**: 10/10 PASS (100.0% compliance).
- **Intended Usage**: Automated parser unit tests and multi-range VTY verification.

#### `edge_cases/partial_vty_failure.txt`
- **Purpose**: Verifies that if one VTY block is secure (`0 4`) but another is insecure (`5 15` permitting Telnet and lacking access-class), the entire rule evaluation flags a failure.
- **Expected Parser Behavior**: Scopes `vty 0 4` as SSH-only with access-class and `vty 5 15` as Telnet-enabled without access-class.
- **Relevant Rules**: NET-001 (FAIL), NET-007 (FAIL).
- **Expected Outcome**: 8 PASS, 2 FAIL (NET-001 and NET-007 fail) (80.0% compliance).
- **Intended Usage**: Automated tests and manual rule validation.

#### `edge_cases/ambiguous_transport.txt`
- **Purpose**: Tests detection and warning for `transport input all`.
- **Expected Parser Behavior**: Produces warning `"Ambiguous transport input 'all' on line vty 0 4 (permits insecure Telnet)"`.
- **Relevant Rules**: NET-001 (Telnet is permitted by `all`, so NET-001 fails).
- **Expected Outcome**: 9 PASS, 1 FAIL (NET-001 fails) (90.0% compliance).
- **Intended Usage**: Manual verification of warning generation and defensive evaluation.

#### `edge_cases/ntp_peer_only.txt`
- **Purpose**: Tests rule NET-006 when only NTP peers exist without an authoritative NTP server.
- **Expected Parser Behavior**: Emits warning `"NTP peer configured (198.51.100.222), but no authoritative 'ntp server' statement found"`.
- **Relevant Rules**: NET-006.
- **Expected Outcome**: 9 PASS, 0 FAIL, 1 WARNING (NET-006 returns WARNING) (100.0% tested compliance).
- **Intended Usage**: Manual QA and rule warning validation.

#### `edge_cases/local_logging_only.txt`
- **Purpose**: Tests rule NET-005 when local buffered logging is configured without a remote syslog host.
- **Expected Parser Behavior**: Emits warning `"Local logging buffer configured, but no remote syslog host specified"`.
- **Relevant Rules**: NET-005.
- **Expected Outcome**: 9 PASS, 0 FAIL, 1 WARNING (NET-005 returns WARNING) (100.0% tested compliance).
- **Intended Usage**: Manual QA and rule warning validation.

---

### 3. Security & Secret Sanitization

#### `security/plaintext_credentials.txt`
- **Purpose**: Verifies that plaintext passwords (`password 0` and unencrypted line/enable passwords) are identified, flagged, and completely redacted.
- **Expected Parser Behavior**: Detects plaintext secrets on user, enable, console, and VTY lines. Sanitizes all evidence strings to `[REDACTED]`.
- **Relevant Rules**: NET-003, NET-010, sanitization engine.
- **Expected Outcome**: NET-003 and NET-010 FAIL. Raw password strings never appear in evidence, database, or API response.
- **Intended Usage**: Automated security sanitization tests and manual leak-prevention verification.

#### `security/type7_credentials.txt`
- **Purpose**: Verifies detection of weak, reversible Cisco Type 7 passwords.
- **Expected Parser Behavior**: Detects Type 7 hashes; sanitizes evidence to `password 7 [REDACTED]`.
- **Relevant Rules**: NET-003 (FAIL). Plaintext rule NET-010 passes.
- **Expected Outcome**: NET-003 FAILS due to reversible credentials.
- **Intended Usage**: Automated and manual testing of Type 7 detection.

#### `security/tacacs_radius_secrets.txt`
- **Purpose**: Verifies that TACACS and RADIUS pre-shared keys are masked during evidence capture and never stored or returned verbatim.
- **Expected Parser Behavior**: Sanitizes `tacacs-server key`, `tacacs-server host ... key`, `radius-server key`, and `radius-server host ... key` with `[REDACTED]`.
- **Relevant Rules**: Security sanitization, data privacy contract.
- **Expected Outcome**: Raw shared keys are redacted across all evidence fields and database entries.
- **Intended Usage**: Automated sanitization tests and compliance data privacy validation.

#### `security/mixed_secrets.txt`
- **Purpose**: Combines plaintext credentials, Type 7 credentials, TACACS keys, RADIUS keys, and SNMP community strings into a single test configuration.
- **Expected Parser Behavior**: All five secret categories are detected and sanitized.
- **Relevant Rules**: NET-003, NET-010, `sanitize_evidence()`.
- **Expected Outcome**: All sensitive tokens masked with `[REDACTED]`; no raw secret leaked in API response.
- **Intended Usage**: Automated end-to-end security integration tests.

---

### 4. Service Hardening

#### `services/insecure_services_enabled.txt`
- **Purpose**: Tests explicit detection of enabled insecure services (`ip http server`, `ip http secure-server`, `service tcp-small-servers`, `service udp-small-servers`).
- **Expected Parser Behavior**: Flags all four insecure service flags as True.
- **Relevant Rules**: NET-008.
- **Expected Outcome**: 9 PASS, 1 FAIL (NET-008 fails with evidence citing `ip http server`) (90.0% compliance).
- **Intended Usage**: Automated tests and service auditing.

#### `services/insecure_services_disabled.txt`
- **Purpose**: Tests explicit compliance when insecure services are disabled (`no ip http server`, `no service tcp-small-servers`, `no service udp-small-servers`, `no ip source-route`).
- **Expected Parser Behavior**: Extracts explicit disabling evidence statements.
- **Relevant Rules**: NET-008.
- **Expected Outcome**: 10/10 PASS (100.0% compliance; NET-008 passes with evidence citing `no ip http server`).
- **Intended Usage**: Automated tests and service hardening validation.

---

### 5. Rule-Specific Scenarios & Diagnostic Isolations

Each rule fixture isolates a single security condition so that diagnostic failure causes can be tested with precision.

| Scenario File | Target Rule | Targeted Condition | Expected Target Status | Total Score |
|---|---|---|---|---|
| `scenarios/net001_telnet.txt` | NET-001 | Telnet permitted on VTY (`transport input telnet`) | **FAIL** | 90.0% (9P, 1F) |
| `scenarios/net002_no_ssh.txt` | NET-002 | SSH version 2 statement absent | **FAIL** | 90.0% (9P, 1F) |
| `scenarios/net003_weak_credentials.txt` | NET-003 | Reversible Type 7 password configured | **FAIL** | 90.0% (9P, 1F) |
| `scenarios/net004_no_login_protection.txt` | NET-004 | `login block-for` rate-limiting absent | **FAIL** | 90.0% (9P, 1F) |
| `scenarios/net005_no_logging.txt` | NET-005 | Remote `logging host` absent | **FAIL** | 90.0% (9P, 1F) |
| `scenarios/net006_no_ntp.txt` | NET-006 | Authoritative `ntp server` absent | **FAIL** | 90.0% (9P, 1F) |
| `scenarios/net007_no_access_class.txt` | NET-007 | `access-class` missing on VTY lines | **FAIL** | 90.0% (9P, 1F) |
| `scenarios/net008_insecure_services.txt` | NET-008 | HTTP and small servers enabled | **FAIL** | 90.0% (9P, 1F) |
| `scenarios/net009_no_banner.txt` | NET-009 | Legal warning banner absent | **FAIL** | 90.0% (9P, 1F) |
| `scenarios/net010_plaintext_secret.txt` | NET-010 | Plaintext credential configured | **FAIL** | 80.0% (8P, 2F: NET-003 & NET-010) |

---

### 6. Positive Controls & Demos

#### `scenarios/all_security_controls.txt`
- **Purpose**: Full-sized positive control configuration satisfying all 10 baseline compliance checks.
- **Expected Outcome**: 10/10 PASS (100.0% compliance).
- **Intended Usage**: Manual demo and automated golden baseline.

#### `scenarios/minimal_secure_router.txt`
- **Purpose**: Validates that compliance passes on minimal syntax without requiring unrelated interface or routing configurations.
- **Expected Outcome**: 10/10 PASS (100.0% compliance).
- **Intended Usage**: Automated test proving the parser does not depend on unrelated configuration lines.

#### `scenarios/remediation_demo.txt`
- **Purpose**: Generates actionable, structured remediation commands across HIGH, MEDIUM, and LOW severity levels for product demonstrations and frontend testing.
- **Expected Outcome**: 0/10 PASS, 10/10 FAIL (0.0% compliance).
- **Remediations Produced**:
  - **HIGH**: Enforce SSH on VTY (`transport input ssh`), enable SSH v2 (`ip ssh version 2`), replace plaintext passwords with strong hashes, apply administrative access-class.
  - **MEDIUM**: Configure brute-force protection (`login block-for 300 attempts 3 within 60`), configure remote syslog host, configure authoritative NTP server.
  - **LOW**: Disable HTTP server and small servers, configure legal warning banner.
- **Intended Usage**: Manual product demos and frontend remediation UI testing.

#### `scenarios/multi_device_secondary.txt`
- **Purpose**: Tested alongside other configurations (`CORE-RTR-01`, `DEFAULT-RTR`) to verify multi-file upload, multi-device persistence, and correct aggregate scan scoring.
- **Hostname**: `BRANCH-RTR-02`.
- **Expected Outcome**: 7 PASS (SSH, credentials, banner, ACL, disabled services), 3 FAIL (login rate-limiting, logging, NTP) (70.0% compliance).
- **Intended Usage**: Manual multi-file scan demonstrations and automated multi-device aggregation tests.

#### `scenarios/executive_demo.txt`
- **Purpose**: Production-grade showcase configuration for executive demonstrations (`CORP-CORE-GW-01`).
- **Expected Outcome**: 10/10 PASS (100.0% compliance, zero warnings).
- **Intended Usage**: Executive presentations and live product walkthroughs.

---

## Manual QA Matrix

The table below reflects **actual observed and empirically verified results** produced by executing the entire fixture suite through the Phoenix Protocol scanner and rule engine (`python -m tests.verify_fixtures`):

| Fixture Path | What it Tests | Device Name | Observed Status | P | F | W | E | Compliance Score |
|---|---|---|---|---|---|---|---|---|
| `compliant_router.txt` | Canonical happy path | `CORE-RTR-01` | success | 10 | 0 | 0 | 0 | 100.0% |
| `failing_router.txt` | Canonical failure baseline | `DEFAULT-RTR` | success | 0 | 10 | 0 | 0 | 0.0% |
| `ambiguous_router.txt` | Incomplete config & warnings | `ambiguous_router` | success | 1 | 5 | 4 | 0 | 16.7% |
| `baseline/compliant_router.txt` | Categorized compliant control | `CORE-RTR-01` | success | 10 | 0 | 0 | 0 | 100.0% |
| `baseline/failing_router.txt` | Categorized failing control | `DEFAULT-RTR` | success | 0 | 10 | 0 | 0 | 0.0% |
| `baseline/ambiguous_router.txt` | Categorized ambiguous control | `ambiguous_router` | success | 1 | 5 | 4 | 0 | 16.7% |
| `edge_cases/empty.txt` | Zero-byte empty file | `empty` | failed | 0 | 0 | 0 | 10 | 0.0% |
| `edge_cases/garbage.txt` | Non-network invalid text | `garbage` | success | 1 | 5 | 4 | 0 | 16.7% |
| `edge_cases/partial_config.txt` | Cisco fragment without baseline | `FRAGMENT-RTR-01` | success | 1 | 6 | 3 | 0 | 14.3% |
| `edge_cases/malformed_banner.txt` | Deliberately unclosed banner | `MALFORMED-BANNER-RTR` | partial | 3 | 6 | 1 | 0 | 33.3% |
| `edge_cases/no_banner.txt` | Valid router missing banner | `NO-BANNER-RTR-01` | success | 9 | 1 | 0 | 0 | 90.0% |
| `edge_cases/multiple_vty_blocks.txt` | Multi-range VTY (all secure) | `SEC-MULTIVTY-RTR` | success | 10 | 0 | 0 | 0 | 100.0% |
| `edge_cases/partial_vty_failure.txt` | Multi-range VTY (one insecure) | `PARTIAL-VTY-RTR` | success | 8 | 2 | 0 | 0 | 80.0% |
| `edge_cases/ambiguous_transport.txt` | Ambiguous `transport input all` | `AMBIG-TRANS-RTR` | success | 9 | 1 | 0 | 0 | 90.0% |
| `edge_cases/ntp_peer_only.txt` | NTP peer without NTP server | `PEER-NTP-RTR` | success | 9 | 0 | 1 | 0 | 100.0% |
| `edge_cases/local_logging_only.txt` | Local log buffer without syslog | `LOCAL-LOG-RTR` | success | 9 | 0 | 1 | 0 | 100.0% |
| `security/plaintext_credentials.txt` | Plaintext credential detection | `PLAIN-SECRETS-RTR` | success | 1 | 8 | 1 | 0 | 11.1% |
| `security/type7_credentials.txt` | Reversible Type 7 detection | `TYPE7-SECRETS-RTR` | success | 2 | 7 | 1 | 0 | 22.2% |
| `security/tacacs_radius_secrets.txt` | AAA key masking & sanitization | `AAA-SECRETS-RTR` | success | 2 | 7 | 1 | 0 | 22.2% |
| `security/mixed_secrets.txt` | Multi-source secret sanitization | `MIXED-SECRETS-RTR` | success | 1 | 8 | 1 | 0 | 11.1% |
| `services/insecure_services_enabled.txt` | HTTP & small servers enabled | `INSEC-SERVICES-ON-RTR` | success | 9 | 1 | 0 | 0 | 90.0% |
| `services/insecure_services_disabled.txt` | Insecure services disabled | `INSEC-SERVICES-OFF-RTR` | success | 10 | 0 | 0 | 0 | 100.0% |
| `scenarios/net001_telnet.txt` | Isolated NET-001 check | `NET001-TELNET-RTR` | success | 9 | 1 | 0 | 0 | 90.0% |
| `scenarios/net002_no_ssh.txt` | Isolated NET-002 check | `NET002-NOSSH-RTR` | success | 9 | 1 | 0 | 0 | 90.0% |
| `scenarios/net003_weak_credentials.txt` | Isolated NET-003 check | `NET003-WEAKPW-RTR` | success | 9 | 1 | 0 | 0 | 90.0% |
| `scenarios/net004_no_login_protection.txt` | Isolated NET-004 check | `NET004-NOLFP-RTR` | success | 9 | 1 | 0 | 0 | 90.0% |
| `scenarios/net005_no_logging.txt` | Isolated NET-005 check | `NET005-NOLOG-RTR` | success | 9 | 1 | 0 | 0 | 90.0% |
| `scenarios/net006_no_ntp.txt` | Isolated NET-006 check | `NET006-NONTP-RTR` | success | 9 | 1 | 0 | 0 | 90.0% |
| `scenarios/net007_no_access_class.txt` | Isolated NET-007 check | `NET007-NOACL-RTR` | success | 9 | 1 | 0 | 0 | 90.0% |
| `scenarios/net008_insecure_services.txt` | Isolated NET-008 check | `NET008-INSECSVC-RTR` | success | 9 | 1 | 0 | 0 | 90.0% |
| `scenarios/net009_no_banner.txt` | Isolated NET-009 check | `NET009-NOBANNER-RTR` | success | 9 | 1 | 0 | 0 | 90.0% |
| `scenarios/net010_plaintext_secret.txt` | Isolated NET-010 check | `NET010-PLAINPW-RTR` | success | 8 | 2 | 0 | 0 | 80.0% |
| `scenarios/all_security_controls.txt` | Compact positive control | `SECURE-CORE-RTR` | success | 10 | 0 | 0 | 0 | 100.0% |
| `scenarios/minimal_secure_router.txt` | Minimal syntax positive control | `MIN-SEC-RTR` | success | 10 | 0 | 0 | 0 | 100.0% |
| `scenarios/remediation_demo.txt` | Multi-severity remediation demo | `REMEDIATION-DEMO-RTR` | success | 0 | 10 | 0 | 0 | 0.0% |
| `scenarios/multi_device_secondary.txt` | Secondary device for multi-scan | `BRANCH-RTR-02` | success | 7 | 3 | 0 | 0 | 70.0% |
| `scenarios/executive_demo.txt` | Executive showcase gateway | `CORP-CORE-GW-01` | success | 10 | 0 | 0 | 0 | 100.0% |

*Note on compliance score calculation*: The compliance engine calculates score using the formula `(passed / (passed + failed)) * 100`. Rules evaluated as `warning`, `not_applicable`, or `error` are not included in the denominator per compliance specification.
