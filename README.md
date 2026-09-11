# Phoenix Protocol

## Project Overview

**Phoenix Protocol** is an adaptive, agentic network security compliance auditor. It helps security administrators inspect network-device configuration files, identify security weaknesses, explain why those weaknesses matter, and recommend vendor-specific corrections.

> **Phoenix Protocol is a web application that turns complex network configurations into clear security findings and practical remediation steps.**

## What the Project Does

A user uploads a configuration from a network device. Phoenix Protocol identifies the device vendor and platform, interprets the configuration, converts it into a common security format, and evaluates it against selected compliance rules.

The system then presents the results in a dashboard. Each finding includes the relevant configuration evidence, the failed security requirement, its severity, the user's compliance score, and a suggested correction.

The system is designed to support configurations from multiple vendors, including Cisco, Juniper, Fortinet, and Palo Alto. It can also handle unfamiliar configuration commands through its adaptive **Teach the Auditor** feature.

## Core Workflow

```text
Configuration upload
        ↓
Vendor and platform discovery
        ↓
Configuration normalization
        ↓
Compliance evaluation
        ↓
Risk and severity analysis
        ↓
Vendor-specific remediation
        ↓
Human review and approval
        ↓
Compliance report
```

## Main Features

| Feature | Description |
|---|---|
| Configuration upload | Accepts network configuration files and, where supported, configuration exports or screenshots. |
| Vendor discovery | Identifies the likely vendor, operating system, device type, and version. |
| Normalization | Converts different vendor syntaxes into a shared security configuration schema. |
| Compliance analysis | Checks the normalized configuration against a curated set of CIS, NIST, STIG, or similar rules. |
| Evidence-based findings | Shows the exact configuration line or property that caused a finding. |
| Risk scoring | Classifies issues as Critical, High, Medium, or Low and calculates an overall score. |
| Remediation guidance | Suggests a vendor-specific command or configuration change. |
| Teach the Auditor | Lets an administrator define the meaning of an unfamiliar command and save the mapping for future audits. |
| Human approval | Prevents potentially risky remediation actions from being executed automatically. |
| Reporting | Produces a readable compliance report, including findings, evidence, scores, and recommendations. |

## What Makes It Different

The main differentiator is that Phoenix Protocol is not limited to a fixed list of known configuration formats. When it encounters an unfamiliar command, it can ask an administrator to explain the command's security meaning. The system stores that explanation as a reusable configuration mapping.

This means Phoenix Protocol learns **configuration mappings**, not model weights. The feature should therefore be described as an **adaptive configuration knowledge base**, rather than as AI model retraining.

## Role of Artificial Intelligence

Phoenix Protocol uses artificial intelligence where interpretation is useful and deterministic rules where security decisions must be reliable.

| Responsibility | Responsible component |
|---|---|
| Understand what a configuration command means | AI agents |
| Convert vendor syntax into a common schema | Normalization agent and validated schemas |
| Decide whether a security requirement passes or fails | Curated deterministic compliance rules |
| Explain findings and estimate interpretation confidence | AI agents and audit metadata |
| Suggest how to correct a finding | Remediation agent with human review |

The guiding principle is:

> **AI decides what the configuration means. Rules decide whether it is compliant. AI suggests how to remediate it.**

## Agent Architecture

The project can use Google Agent Development Kit (ADK) to coordinate specialized agents:

- **Root Agent:** Coordinates the complete audit process.
- **Discovery Agent:** Identifies the vendor, platform, model, version, and configuration format.
- **Normalization Agent:** Translates vendor-specific syntax into a common security schema.
- **Compliance Agents:** Evaluate the normalized configuration against selected frameworks. Independent framework checks can run in parallel.
- **Risk Agent:** Combines findings into severity levels and an overall compliance score.
- **Remediation Agent:** Generates vendor-specific correction guidance.

A simplified execution sequence is:

```text
Root Agent
    ├── Discovery Agent
    ├── Normalization Agent
    ├── CIS / NIST / STIG checks in parallel
    ├── Risk Agent
    └── Remediation Agent
```

## Product Type

Phoenix Protocol should be built as a **desktop-focused web application**, not as a mobile application.

A web application is appropriate because the product requires file uploads, detailed security tables, expandable evidence, audit-progress views, remediation review, and report downloads. Security administrators will normally use it from a laptop or desktop browser.

The project may include a small landing page, but the primary deliverable should be the working audit dashboard.

## Recommended MVP Scope

The first version should focus on a reliable and impressive demonstration rather than claiming complete support for every network vendor or every compliance framework.

The MVP should support a small number of known vendors, approximately 15–30 carefully reviewed compliance rules, evidence-based findings, severity scoring, vendor-specific remediation, PDF reporting, and the Teach the Auditor workflow.

The project should not attempt to implement full framework coverage, live access to many network devices, actual model training, Kubernetes deployment, or complex enterprise authentication during the initial hackathon version.

## Suggested Demonstration

The demonstration should follow this sequence:

1. Upload a Cisco, Juniper, Fortinet, or Palo Alto configuration.
2. Show the detected vendor and platform.
3. Display the normalization progress.
4. Run multiple compliance checks.
5. Open a failed finding and show its evidence.
6. Display the risk severity and compliance score.
7. Show the vendor-specific remediation command.
8. Upload or reveal an unfamiliar configuration command.
9. Use **Teach the Auditor** to define its meaning.
10. Run the audit again and show that the command is now understood.

This demonstrates both the practical security value and the adaptive agentic capability of Phoenix Protocol.

## One-Sentence Description

> **Phoenix Protocol is an adaptive web-based network security compliance auditor that uses AI agents to understand multi-vendor configurations, deterministic rules to evaluate security, and human-approved remediation to help organizations secure their network infrastructure.**

## Suggested Tagline

> **Rise above configuration complexity. Secure every network.**

## Backend API & Developer Documentation

### Installation & Environment Setup

```bash
# Install dependencies
pip install -r requirements.txt
```

### Running Tests

```bash
# Run complete test suite (Track 2 core + Flask API)
python -m pytest -v
```

### Running the Flask API Server

```bash
# Run using Flask CLI
flask --app "app.api:create_app()" run --port 5000
```

Or programmatically in Python:
```python
from app.api import create_app

app = create_app()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
```

### API Endpoints

#### 1. `GET /health`
Returns service operational health metadata.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "phoenix-protocol",
  "version": "1.0.0"
}
```

#### 2. `POST /scan`
Uploads one or more network device configuration files and triggers deterministic compliance analysis.

- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `file` or `files`: One or more configuration files (up to 10 MB each).
  - `device_type` (optional): Requested device profile. Currently supported: `cisco_ios` (default).

**Response (201 Created):**
```json
{
  "scan_id": "scan_b2c47a59e...",
  "status": "completed",
  "device_type": "cisco_ios",
  "parser_version": "1.0.0",
  "rule_set_version": "1.0.0",
  "summary": {
    "total_rules": 10,
    "passed_rules": 10,
    "failed_rules": 0,
    "warning_rules": 0,
    "not_applicable_rules": 0,
    "error_rules": 0,
    "tested_rule_compliance": 100.0
  },
  "compliance_score": 100.0,
  "devices": [
    {
      "device_id": "9b1deb4d...",
      "name": "CORE-RTR-01",
      "display_name": "CORE-RTR-01",
      "vendor": "Cisco",
      "device_type": "cisco_ios",
      "source_filename": "core_rtr.cfg",
      "parse_status": "success",
      "line_count": 85,
      "error_message": null,
      "summary": {
        "total_rules": 10,
        "passed_rules": 10,
        "failed_rules": 0,
        "warning_rules": 0,
        "not_applicable_rules": 0,
        "error_rules": 0,
        "tested_rule_compliance": 100.0
      },
      "compliance_score": 100.0,
      "results": [
        {
          "rule_id": "NET-001",
          "status": "pass",
          "severity": "high",
          "evidence": "transport input ssh",
          "evidence_line_range": "45-46",
          "message": "Telnet is disabled on all administrative VTY line blocks (SSH-only enforced).",
          "remediation": "line vty 0 4\n transport input ssh"
        }
      ]
    }
  ]
}
```

#### 3. `GET /scans/<scan_id>`
Retrieves a previously evaluated scan by its unique scan ID directly from SQLite persistence.

- **Response (200 OK)**: Standardized Phoenix Protocol scan result matching the contract above.
- **Response (404 Not Found)**: `{"error": "Scan not found", "detail": "...", "scan_id": "..."}`

## ADK Teach-the-Auditor Intelligence Layer

Teach-the-Auditor is Phoenix Protocol's adaptive intelligence component powered by the Google Agent Development Kit (ADK). When an unfamiliar network configuration command is encountered during parsing or auditing, Teach-the-Auditor interprets its security semantics without replacing deterministic compliance evaluation.

### Architecture & Trust Boundary

```text
UnknownCommand
    ↓
TeachAuditorService
    ↓
KnowledgeProvider (Tool: lookup_known_command)
    ├── [FOUND]     → Trusted interpretation (requires_human_approval = False)
    └── [NOT FOUND] → Google ADK Agent (output_schema: CommandInterpretation)
                            ↓
                      TeachingProposal (requires_human_approval = True)
                            ↓
                      (Human Review & Dev2 KnowledgeService Persistence)
```

The core trust boundary is strictly enforced:
- **AI understands syntax and explains security meaning.**
- **Deterministic rules evaluate whether a configuration passes or fails.**
- **High-consequence actions (learning/persistence) require human approval.**
- Under no circumstances does the agent produce `pass`/`fail` compliance verdicts.

### 1. Agent Input Contract (`UnknownCommand`)

Defined in `app/agents/schemas.py`:

```python
class UnknownCommand(BaseModel):
    vendor: str                         # e.g., 'Cisco', 'Arista', 'Juniper'
    platform: str                       # e.g., 'IOS', 'EOS', 'JunOS'
    command: str                        # Raw or normalized command string
    context: Optional[Union[str, List[str]]] = None  # Surrounding config block
    source_line: Optional[int] = None   # 1-based source line number
```

### 2. Agent Output Contract (`CommandInterpretation`)

Structured output produced by the ADK agent and validated with Pydantic:

```python
class CommandInterpretation(BaseModel):
    command: str                        # Target command string
    vendor: str                         # Target vendor
    platform: str                       # Target platform
    meaning: str                        # Concise operational explanation
    security_control: str               # Control area (e.g. transport_security, logging)
    mapped_rule_id: Optional[str] = None # Optional NET-001..NET-010 or null
    confidence: float                   # Strictly bounded: 0.0 <= confidence <= 1.0
    explanation: str                    # Semantic rationale justifying mapping
```

- `mapped_rule_id` is strictly optional (`None` is permitted). The LLM is never forced to invent rule IDs.
- Invented or hallucinated rule IDs outside the curated catalog (`NET-001` through `NET-010`) are rejected at the schema validation boundary.

### 3. KnowledgeProvider Interface (`app/agents/knowledge.py`)

Abstract interface decoupling Teach-the-Auditor from any specific database implementation:

```python
class KnowledgeProvider(ABC):
    @abstractmethod
    def lookup_command(
        self, vendor: str, platform: str, command: str
    ) -> Optional[CommandInterpretation]:
        """Look up an existing verified interpretation for a command."""
        raise NotImplementedError
```

- **`MockKnowledgeProvider`**: In-memory, case- and whitespace-insensitive reference implementation used for deterministic unit testing and offline development.
- The agent accesses this abstraction through a single dedicated tool: `lookup_known_command()`.

### 4. Human Approval Boundary (`TeachingProposal`)

AI-generated interpretations are packaged into a proposal enforcing human review:

```python
class TeachingProposal(BaseModel):
    interpretation: CommandInterpretation
    requires_human_approval: bool = True  # Always True for new AI interpretations
    source: str = "ai_agent"              # 'knowledge_base' or 'ai_agent'
```

- Newly generated AI interpretations are never silently committed or persisted.
- Pre-existing mappings loaded from the `KnowledgeProvider` set `requires_human_approval = False` as they have already undergone prior verification.

### 5. Why AI Does Not Determine Compliance

In Phoenix Protocol:
1. **Determinism**: Regulatory compliance (e.g., CIS, NIST, PCI-DSS) requires mathematically reproducible audits. Two scans of identical configurations must yield identical scores.
2. **Audit Defensibility**: Security findings must cite verifiable evidence and deterministic rule logic rather than probabilistic LLM outputs.
3. **Role Separation**: AI interprets ambiguous syntax (e.g., unfamiliar vendor commands); deterministic rules evaluate compliance against security thresholds; humans authorize policy additions.

### 6. Dev2 KnowledgeService Integration Point

Dev2 is independently developing the persistent `KnowledgeService` in her branch/component. Once complete, integration requires zero changes to the ADK agent or schemas:

1. Dev2's service will provide persistent storage (e.g., SQLite/PostgreSQL) with `lookup_command()`, `propose_mapping()`, `approve_mapping()`, and `reject_mapping()`.
2. An adapter implementing `KnowledgeProvider` will wrap her `KnowledgeService.lookup_command()`.
3. When `TeachingProposal` is approved by a human administrator, the proposal will be forwarded to her `approve_mapping()` method for long-term persistence.

## References

[1]: https://google.github.io/adk-docs/ "Google Agent Development Kit Documentation"

[2]: https://www.cisecurity.org/controls "CIS Critical Security Controls"


