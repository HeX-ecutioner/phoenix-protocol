# Product Requirements Document: Network Compliance Scanner

**Document status:** Hackathon MVP proposal  
**Audience:** Beginner development team, judges, mentors, and early users  
**Primary user:** Network administrator or security analyst managing exported configurations  
**Recommended first device type:** One Cisco-like network-device configuration format  
**Product mode:** Read-only assessment; no automatic production changes

## 1. Product name

**Phoenix Protocol**

The name communicates that the product protects an organization by checking device configurations. It is short, easy to remember, and suitable for a hackathon demo.

## 2. One-line product description

**Phoenix Protocol scans uploaded network-device configuration files against transparent security rules and produces an evidence-based compliance report with prioritized remediation guidance.**

## 3. Problem statement

Organizations often manage hundreds or thousands of routers, switches, firewalls, wireless controllers, and virtual network appliances. Each device contains security settings that must follow internal policies or recognized security standards.

Checking those settings manually is slow and inconsistent. Administrators may need to log in to devices individually, search for configuration lines, compare them with a checklist, and record the results in a spreadsheet. Different vendors also express similar settings in different formats.

Existing approaches can be expensive, vendor-specific, difficult to maintain, or too technical for smaller teams. Users need a safe and repeatable way to determine which devices appear compliant, which devices have high-risk configuration failures, and what evidence supports each result.

Phoenix Protocol addresses **configuration compliance**, not every possible security problem. A passing result means that the tested rules appear satisfied. It does not prove that a device is completely secure.

## 4. Target users

### Primary users

| User | Need | Product value |
|---|---|---|
| Network administrator | Quickly identify unsafe settings across many devices | Scans multiple files in one operation |
| Security analyst | Collect consistent evidence for configuration checks | Shows rule, result, evidence, severity, and remediation |

### Secondary users

| User | Need | Product value |
|---|---|---|
| IT operations manager | Understand overall configuration risk | Views summary counts and high-risk issues |
| Compliance auditor | Review repeatable assessment evidence | Downloads a dated report |
| Small-company IT generalist | Understand technical findings | Receives plain-language explanations |

The initial MVP is designed for a technical user who can export or obtain sanitized device configuration files. It is not initially designed for non-technical business users to configure security policies themselves.

## 5. User pain points

1. **Manual inspection does not scale.** Checking devices one at a time consumes significant time.
2. **Human reviews vary.** Different administrators may interpret the same requirement differently.
3. **Configuration syntax differs by vendor.** A rule that is simple for one device type may require different parsing for another.
4. **Security standards are not directly executable.** A requirement such as “use secure administration” must be translated into a precise test.
5. **Raw technical output is hard to understand.** Users need an explanation of the risk, not only a failed command search.
6. **Evidence is easy to lose.** Users need to know which configuration line produced each result.
7. **Direct device access introduces risk.** Credentials, permissions, network connectivity, and production impact complicate a first version.
8. **Remediation can be dangerous.** An incorrect change may interrupt connectivity, so recommendations should be reviewed before execution.

## 6. Proposed solution

Phoenix Protocol is a read-only web application with the following workflow:

1. The user uploads one or more sanitized configuration files.
2. The user selects the device type, or the application identifies it when possible.
3. A parser extracts security-relevant settings from each file.
4. A deterministic rule engine evaluates a small, transparent rule library.
5. The application reports **Pass**, **Fail**, **Warning**, **Not applicable**, or **Error** for each rule.
6. The user sees the evidence, risk explanation, severity, and suggested next step.
7. The user downloads a CSV or HTML report.

The initial release supports one vendor format and approximately 10 rules. It does not connect to live production devices or automatically modify configurations.

## 7. Product goals

### Primary goals

- Reduce the time needed to assess multiple network-device configurations.
- Produce repeatable results for the same input and rule version.
- Make every result understandable to a beginner or generalist.
- Show evidence for each pass, fail, warning, or error.
- Help users prioritize high-severity failures.
- Provide a useful, polished demonstration within a short hackathon.

### Secondary goals

- Separate vendor-specific parsing from general compliance rules.
- Make the rule library easy to inspect and extend.
- Produce a report that can be shared with a mentor, manager, or auditor.
- Keep the product safe by avoiding production changes and real credentials.

### Non-goals

- Proving that a device is completely secure.
- Replacing a full vulnerability scanner.
- Automatically fixing production configurations.
- Supporting every vendor or security framework in the first release.

## 8. User stories

| ID | User story | Priority |
|---|---|---|
| US-01 | As a network administrator, I want to upload several configuration files so that I can assess multiple devices in one scan. | Must have |
| US-02 | As a user, I want to select the device type so that the correct parser and rules are applied. | Must have |
| US-03 | As a security analyst, I want to see pass/fail/warning results for each rule so that I can understand device compliance. | Must have |
| US-04 | As a security analyst, I want to see the configuration evidence behind a result so that I can verify the finding. | Must have |
| US-05 | As a beginner, I want a plain-language explanation of a failed rule so that I understand why it matters. | Must have |
| US-06 | As an administrator, I want high-severity failures shown first so that I can prioritize investigation. | Must have |
| US-07 | As an auditor, I want to download a report containing scan details and evidence so that I can retain an assessment record. | Must have |
| US-08 | As a user, I want ambiguous settings to produce a warning rather than a false pass or fail. | Should have |
| US-09 | As an operations manager, I want a summary dashboard so that I can quickly understand the overall result. | Should have |
| US-10 | As a future rule author, I want rules to have structured metadata so that I can add checks consistently. | Should have |
| US-11 | As a multi-vendor administrator, I want different vendor configurations mapped to common security concepts so that rules can eventually be reused. | Could have |
| US-12 | As a user, I want an AI-generated summary of the scan so that I can communicate the main findings quickly. | Could have |

## 9. Functional requirements

### FR-01: Upload configuration files

The system shall allow the user to upload one or more text configuration files in a supported format.

The system shall show the filename and upload status. The system shall reject unsupported file types and files larger than the configured limit.

### FR-02: Select device type

The system shall allow the user to select the supported vendor or device type before scanning.

Automatic detection may be added later, but manual selection is acceptable for the MVP.

### FR-03: Parse configurations

The system shall extract relevant values from supported configuration text, such as whether secure administration, logging, time synchronization, and insecure services are enabled.

The parser shall preserve line numbers or source snippets when possible so that rule results can show evidence.

### FR-04: Maintain a rule library

Each rule shall contain at least:

- Rule identifier.
- Title.
- Plain-language explanation.
- Technical requirement.
- Applicable device type.
- Severity.
- Evaluation logic.
- Evidence field or source snippet.
- Remediation guidance.

### FR-05: Evaluate rules

The system shall run all applicable rules against every uploaded configuration.

Each result shall use one of these statuses:

| Status | Definition |
|---|---|
| Pass | The available evidence satisfies the rule |
| Fail | The available evidence violates the rule |
| Warning | The system cannot make a confident determination or manual review is required |
| Not applicable | The rule does not apply to the selected device type |
| Error | Parsing or evaluation failed |

### FR-06: Display results

The system shall display results by device and by rule.

The system shall show severity, status, evidence, explanation, and remediation guidance for each evaluated rule.

### FR-07: Prioritize findings

The system shall sort or filter results by severity and status. High-severity failures shall be easy to identify.

### FR-08: Show summary metrics

The dashboard shall show at least:

- Number of devices scanned.
- Total rules evaluated.
- Counts of pass, fail, warning, not applicable, and error results.
- Number of high-severity failures.
- A clearly labeled summary compliance percentage, if calculated.

The application shall explain how the percentage is calculated and shall not present it as a complete security score.

### FR-09: Export a report

The system shall allow the user to download a CSV or HTML report containing:

- Scan timestamp.
- Device filename or identifier.
- Selected device type.
- Rule identifier and title.
- Status.
- Severity.
- Evidence.
- Explanation.
- Remediation guidance.

### FR-10: Provide safe remediation guidance

The system shall provide suggested next steps without executing changes. Guidance shall include a warning that production changes require review and testing.

### FR-11: Handle errors

The system shall identify unreadable files, unsupported syntax, and incomplete data. It shall show an actionable error or warning instead of silently ignoring the problem.

### FR-12: Protect demo data

The system shall not require real device passwords for the MVP. It shall use sanitized or synthetic configuration files for demonstrations.

## 10. Non-functional requirements

### Usability

- A first-time user should be able to complete a scan without reading technical documentation.
- The interface shall use plain language alongside technical terms.
- The primary workflow should be visible from the landing screen.
- Failed checks should not be communicated only through color; the status text must also be visible.

### Performance

- A scan of at least three to five small configuration files should complete within a few seconds on a local hackathon deployment.
- The interface should show progress or a loading state during scanning.

### Reliability

- The same input, rule set, and parser version should produce the same results.
- One invalid file should not prevent valid files from being scanned.
- Rule evaluation errors should be recorded and shown to the user.

### Security and privacy

- The application shall not execute commands found in uploaded files.
- Uploaded filenames shall be sanitized.
- File size and type limits shall be enforced.
- The application shall avoid logging complete configuration contents.
- The demo shall use fake or sanitized configurations.
- Direct device connections and credential storage are excluded from the MVP.

### Maintainability

- Parser logic and compliance logic should be separate modules.
- Rules should have stable identifiers and structured metadata.
- Core parsing and rule behavior should have automated tests.

### Accessibility

- Results should be readable using keyboard navigation.
- Status should be represented by text and not only by color.
- Tables should have clear headings.

## 11. Core features

### 11.1 Multi-file upload

A drag-and-drop area or file picker lets a user submit several configurations at once.

### 11.2 Supported-device selector

A simple dropdown identifies the parser and rule set. The MVP can support one device type while showing how more types could be added.

### 11.3 Transparent rule library

A rule details view explains what each rule checks and why it matters.

### 11.4 Compliance scan

A scan action runs the parser and rule engine against all selected files.

### 11.5 Results dashboard

The dashboard shows overall counts and highlights high-severity failures.

### 11.6 Device detail page

The user can select a device and inspect each rule result, including source evidence.

### 11.7 Remediation guidance

Each failure includes a safe, human-readable recommendation. The MVP should avoid presenting unverified commands as automatically safe.

### 11.8 Report export

The user can download a CSV or HTML report for sharing or record keeping.

## 12. Nice-to-have features

These features may be added only after the core scan works:

- Support for a second vendor.
- Automatic vendor detection.
- YAML-based custom rules.
- Rule mapping to CIS Benchmarks, NIST controls, or internal policies.
- Scan history and trend charts.
- Direct read-only SSH or API collection.
- Configuration drift alerts.
- User accounts and role-based permissions.
- Slack, email, ticketing, or SIEM integrations.
- Optional AI-generated summary of already-determined findings.
- Multilingual explanations.

## 13. User journeys

### Journey A: First scan

1. The user opens Phoenix Protocol.
2. The home page explains that the product checks configuration files and does not modify devices.
3. The user selects the supported device type.
4. The user uploads three sanitized configuration files.
5. The user clicks **Run compliance scan**.
6. The system parses each file and evaluates the applicable rules.
7. The system displays the dashboard.

### Journey B: Investigate a high-risk finding

1. The user sees that one device has three high-severity failures.
2. The user opens the device details page.
3. The user filters the results to high severity.
4. The user opens the failed secure-administration rule.
5. The system shows the relevant configuration evidence.
6. The system explains the risk in plain language.
7. The system gives a suggested next step and states that changes require review.

### Journey C: Review an ambiguous configuration

1. The user sees a warning instead of a pass or fail.
2. The user opens the warning.
3. The system explains what evidence was missing or ambiguous.
4. The user knows what manual check is needed.

### Journey D: Share results

1. The user finishes reviewing the scan.
2. The user clicks **Download report**.
3. The system generates a CSV or HTML file.
4. The report includes the scan timestamp, device identifiers, rule results, evidence, and remediation guidance.

## 14. MVP scope

### Included in the MVP

- Web-based interface.
- Upload of at least three text configuration files.
- One supported vendor or device format.
- Approximately 10 deterministic security rules.
- Pass, fail, warning, not applicable, and error statuses.
- Evidence snippets or line references.
- Severity prioritization.
- Summary dashboard.
- Device-level result details.
- CSV or HTML report export.
- Sanitized sample configuration files.
- Basic validation and safe file handling.
- Automated tests for parser and rule behavior.

### Recommended initial rules

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
| NET-009 | Device ownership or identification metadata is present | Low |
| NET-010 | Obvious plaintext secret patterns are absent | High |

These rules are demonstration examples. They must be validated against the selected vendor’s syntax and the team’s chosen security policy before being presented as authoritative compliance checks.

### Demo dataset

The demo should contain three sanitized devices:

- One mostly compliant device.
- One device with obvious high-risk failures.
- One device with incomplete or ambiguous settings that produce warnings.

This dataset demonstrates the complete product story within a few minutes.

### MVP acceptance criteria

The MVP is complete when:

- At least three configuration files can be scanned in one operation.
- At least eight rules return meaningful results.
- Results are repeatable for the same input.
- Evidence is shown for each evaluated rule when available.
- High-severity failures are clearly prioritized.
- Warnings and parser errors are visible.
- A report can be downloaded.
- No real device credentials are required or stored.
- The demo can be completed from upload to report without developer intervention.

## 15. Out-of-scope features

The following are explicitly excluded from the hackathon MVP:

- Automatic changes to live devices.
- Direct SSH, API, or SNMP collection from production devices.
- Support for every network vendor.
- A complete vulnerability scanner.
- Full implementation of every security framework.
- Enterprise identity management and complex role administration.
- Automatic remediation tickets or change approvals.
- Real-time monitoring.
- Guaranteed detection of every secret or misconfiguration.
- A security score presented as proof of complete security.
- Production-grade multi-tenant data isolation.
- Large-scale distributed scanning infrastructure.

## 16. Success metrics

### Hackathon demonstration metrics

| Metric | Target |
|---|---:|
| Configuration files scanned in one run | At least 3 |
| Rules evaluated | At least 8, ideally 10 |
| Scan completion time for demo files | Less than 10 seconds |
| Results with visible evidence | At least 90% where evidence exists |
| Findings with severity and remediation | 100% of failed rules |
| Report export | Works in the live demo |
| Manual developer intervention during demo | None after setup |

### Product usefulness metrics

| Metric | How to measure |
|---|---|
| Time saved compared with manual review | Compare one small batch manually and with Phoenix Protocol |
| Result repeatability | Run the same input twice and compare outputs |
| Finding comprehension | Ask a beginner to explain one failed rule after reading the result |
| False-confidence avoidance | Confirm warnings appear for intentionally incomplete configurations |
| Actionability | Ask a network practitioner whether the evidence and next step are useful |

The team should avoid claiming enterprise-scale accuracy from a small hackathon dataset. Metrics should describe the prototype’s demonstrated behavior.

## 17. Risks and assumptions

### Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Vendor syntax is more complicated than expected | Parser may produce incorrect results | Choose one narrow format and use controlled sample files |
| Rules are too broad or ambiguous | Users may distrust results | Show evidence and use warnings when confidence is low |
| Incorrect remediation advice | A user could make an unsafe change | Provide review warnings and avoid automatic execution |
| Sensitive configuration data is uploaded | Privacy or security exposure | Use sanitized data, limit files, and avoid content logging |
| Dashboard work consumes too much time | Core scanner remains incomplete | Build parser and rules before visual polish |
| AI output is inaccurate | Users may receive misleading explanations | Keep compliance decisions deterministic; use fixed rule text |
| Compliance percentage is misunderstood | Users may assume the product proves security | Label it as tested-rule compliance and show individual findings |
| Scope expands to many vendors | MVP becomes unreliable | Treat one vendor as a firm launch constraint |
| Parser errors are hidden | Users may trust incomplete results | Show errors and warnings explicitly |

### Assumptions

- The user can obtain exported, text-based configuration files.
- The hackathon team can choose one device format for the first implementation.
- The demo can use fake or sanitized configurations.
- The initial rule set can be reviewed by a mentor or security-aware team member.
- A local or simple hosted deployment is sufficient for judging.
- The MVP does not need to change or connect to production devices.
- The selected configuration syntax is stable enough for deterministic parsing.

## Recommended implementation plan

| Phase | Deliverable |
|---|---|
| Phase 1 | Confirm one vendor, define 10 rules, and prepare sample files |
| Phase 2 | Build upload flow and parser |
| Phase 3 | Implement and test deterministic rule functions |
| Phase 4 | Build dashboard and device detail views |
| Phase 5 | Add evidence, remediation, and report export |
| Phase 6 | Test pass, fail, warning, and error scenarios |
| Phase 7 | Rehearse a short demo and document limitations |

## Final product principle

Phoenix Protocol should be **small, safe, explainable, and demonstrable**. A reliable scanner for one device type is a stronger hackathon product than an incomplete platform that claims to support every vendor and standard.

> Phoenix Protocol turns a repetitive security checklist into a fast, evidence-based workflow while keeping administrators in control of production changes.

## References

[1]: https://www.nist.gov/cyberframework "NIST Cybersecurity Framework"

[2]: https://www.cisecurity.org/controls "CIS Critical Security Controls"

[3]: https://www.cisecurity.org/benchmark/network-devices "CIS Benchmarks for Network Devices"

[4]: https://www.ansible.com/use-cases/network-automation "Ansible Network Automation"

[5]: https://www.open-scap.org/ "OpenSCAP Security Compliance Solutions"

