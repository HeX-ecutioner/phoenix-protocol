# Phoenix Protocol — Teach the Auditor Knowledge Layer (Developer 2 Package)

Isolated, lightweight, and deterministic knowledge persistence, validation, sanitization, and approval layer for the **Teach the Auditor** subsystem of Phoenix Protocol.

---

## 1. What This Package Does

- **Command Meaning Storage**: Captures and persists structured mappings describing what network CLI configuration commands mean (e.g. `"transport input ssh"` maps to `security_control = "management_plane_security"` and `mapped_rule_id = "NET-001"`).
- **Human Approval Lifecycle**: Enforces a strict approval state machine (`proposed` -> `approved` | `rejected`). New proposals default to `proposed` and can never be retrieved by normal scan lookups until an authorized human auditor approves them.
- **Strict Validation Pipeline**: Validates incoming payloads (`validate -> normalize -> sanitize -> persist`) ensuring malformed, overlong, or invalid inputs are rejected with clear diagnostics.
- **Defensive Secret Sanitization**: Redacts passwords, pre-shared keys, TACACS/RADIUS keys, community strings, and tokens prior to database persistence, replacing them with `[REDACTED]` while preserving legitimate command syntax.
- **Deterministic Normalization**: Strips leading/trailing whitespace, collapses internal whitespace, and lowercases command syntax to enable canonical, deterministic exact matching.
- **Vendor & Platform Isolation**: Stores knowledge scoped to specific vendor/platform pairs (e.g. Cisco IOS vs Cisco NX-OS vs Juniper Junos) to prevent unsafe cross-platform command interpretation collisions.
- **Audit-Friendly SQLite Storage**: Uses an isolated SQLite database schema with parameterized queries, indexes, and partial unique constraints to guarantee no duplicate approved knowledge while maintaining full history for proposed/rejected records.

---

## 2. What This Package Deliberately Does NOT Do

- **NO Compliance Decisions**: This package stores command meaning and rule mapping metadata only. It **never** decides whether a device, configuration, or command is compliant or non-compliant. The deterministic rule engine (`app/rules/`) remains authoritative for compliance evaluation.
- **NO Remediation Commands**: Does not generate or push remediation commands to devices.
- **NO AI/LLM Logic**: Contains zero LLM/Gemini API calls, prompt engineering, Google ADK agents, A2A communication, or MCP integrations.
- **NO Web / API Framework Code**: Does not contain Flask routes, FastAPI routes, web middleware, or frontend components.
- **NO Network Connections**: Does not connect to physical or virtual network devices.
- **NO Direct Main DB Access**: Does not touch, modify, or depend upon the primary Phoenix Protocol SQLite database (`scans.db`).

---

## 3. Mapping Data Model

Represented by the `KnowledgeMapping` dataclass (`models/knowledge_mapping.py`):

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | `str` (UUID) | Auto | Unique identifier for mapping record |
| `vendor` | `str` | Yes | Target vendor (e.g. `Cisco`, `Juniper`, `Fortinet`, `Palo Alto`) |
| `platform` | `str` | Yes | Target OS platform (e.g. `cisco_ios`, `junos`, `fortios`, `panos`) |
| `command_pattern` | `str` | Yes | Original or sanitized command pattern (e.g. `transport input ssh`) |
| `normalized_command` | `str` | Auto/Yes | Canonical whitespace-collapsed & lowercased string for lookup |
| `meaning` | `str` | Yes | Human-readable explanation of command purpose |
| `security_control` | `str` | Yes | Security capability tag (e.g. `management_plane_security`) |
| `mapped_rule_id` | `Optional[str]`| No | Associated compliance rule identifier (e.g. `NET-001`, `NET-007`) |
| `explanation` | `str` | No | Additional context or rationale |
| `confidence` | `float` | No | Interpretation confidence score bounded between `0.0` and `1.0` (default: `1.0`) |
| `source` | `str` | No | Provenance indicator (e.g. `ai_agent`, `human`) |
| `approval_status` | `str` | Yes | Lifecycle status (`proposed`, `approved`, `rejected`) |
| `created_at` | `str` (ISO-8601) | Auto | Timezone-aware UTC creation timestamp |
| `updated_at` | `str` (ISO-8601) | Auto | Timezone-aware UTC last modification timestamp |
| `version` | `str` | No | Schema version (default: `1.0.0`) |

---

## 4. Approval Workflow

```text
       [ AI Agent / Human Proposal ]
                     │
                     ▼
             validate_payload()
                     │
                     ▼
            normalize_command()
                     │
                     ▼
         sanitize_secret_command()
                     │
                     ▼
          repo.create(status="proposed")
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
  Auditor Approves        Auditor Rejects
         │                       │
         ▼                       ▼
repo.update("approved")  repo.update("rejected")
         │                       │
         ▼                       ▼
 Available for Scanner   Preserved for Audit
   lookup_command()     (Excluded from lookup)
```

1. Proposals enter via `KnowledgeService.propose_mapping(...)` with `approval_status = "proposed"`.
2. Proposals are excluded from production scanner lookups.
3. An auditor calls `KnowledgeService.approve_mapping(mapping_id)`. The system verifies no conflicting approved mapping already exists.
4. If approved, the record is immediately retrievable by `KnowledgeService.lookup_command(...)`.
5. If rejected via `KnowledgeService.reject_mapping(mapping_id)`, the record remains in SQLite for auditability but is excluded from scanner lookups.

---

## 5. Lookup Behavior

The primary lookup method is:

```python
service.lookup_command(vendor="Cisco", platform="cisco_ios", command="  IP SSH VERSION 2  ")
```

- **Approved Only**: Only mappings where `approval_status == 'approved'` are returned. Proposed and rejected records return `None`.
- **Deterministic Match**: Input command text is automatically normalized (whitespace stripped, repeated spaces collapsed, lowercased) before searching.
- **Exact Scoping**: Requires exact case-insensitive matches for `vendor`, `platform`, and `normalized_command`.

---

## 6. Vendor and Platform Isolation

Command syntax often collides across vendors and platforms with completely different security meanings.
For example, `no ip domain-lookup` or `logging host` may behave differently across operating systems.

- Lookups **never** fall back to cross-vendor or cross-platform matching.
- A Cisco IOS mapping is strictly isolated from Cisco NX-OS, Juniper Junos, Fortinet FortiOS, and Palo Alto PAN-OS.
- Multiple vendors can map their respective platform-specific commands to the same conceptual `mapped_rule_id` (e.g. `NET-002`) without collision.

---

## 7. Security and Sanitization Model

Network configuration commands frequently contain embedded credentials. The package treats all command input as untrusted.

### The Pipeline
```text
validate -> normalize -> sanitize -> persist
```

### Redaction Rules
- Passwords (`password [0|7] <secret>` -> `password [REDACTED]`)
- Secret keys (`secret [0|5|8|9] <secret>` -> `secret [REDACTED]`)
- TACACS & RADIUS shared keys (`tacacs-server key <secret>` -> `tacacs-server key [REDACTED]`)
- SNMP community strings (`snmp-server community <secret>` -> `snmp-server community [REDACTED]`)
- API tokens & pre-shared keys (`token <secret>` -> `token [REDACTED]`)

### Guaranteed Invariants
- Raw secret strings **never** reach SQLite database columns.
- Serialized dictionaries, logs, error messages, and API responses never expose unredacted secrets.
- Legitimate non-secret syntax (e.g. `service password-encryption`, `username admin privilege 15`) is preserved intact.

---

## 8. Integration Contract for Developer 1

Developer 1 should import and use **only** the high-level `KnowledgeService` or protocols from `integration_contract.py`.

### Supported Import Patterns

The `knowledge` package is a standard Python package under `backend/`:

```python
from knowledge.services.knowledge_service import KnowledgeService

service = KnowledgeService(db_path="knowledge.db")
```

# 1. Propose mapping from AI Agent
proposal = service.propose_mapping(
    vendor="Cisco",
    platform="cisco_ios",
    command_pattern="ip ssh time-out 60",
    meaning="Sets SSH negotiation timeout to 60 seconds",
    security_control="ssh_timeout",
    mapped_rule_id="NET-009",
    confidence=0.92,
    explanation="Detected from configuration scan",
    source="ai_agent",
)

# 2. Human Auditor approves proposal
approved = service.approve_mapping(proposal.id)

# 3. Auditor rejects proposal
# service.reject_mapping(proposal.id, reason="Incorrect interpretation")

# 4. Scanner Engine queries approved knowledge
match = service.lookup_command("Cisco", "cisco_ios", "ip ssh time-out 60")
if match:
    print(f"Command mapped to rule: {match.mapped_rule_id}")

# 5. Admin lists
proposals = service.list_proposals(vendor="Cisco")
approved_rules = service.list_approved_knowledge(vendor="Cisco")
```

### Integration Rules for Developer 1
1. **Never manipulate SQLite directly**: Do not execute raw SQL against the knowledge database; always use `KnowledgeService`.
2. **Handle DuplicateMappingError**: Catch `DuplicateMappingError` when approving proposals if another approved mapping already exists for the command.
3. **No Compliance Judgments**: The returned `KnowledgeMapping` tells you what rule the command maps to (`mapped_rule_id`). Pass this evidence to the compliance engine; do not make a compliance decision in the service.

---

## 9. Database Location and Isolation

- **Isolated Database**: The knowledge database is completely separate from `scans.db`.
- **Configurable Path**: Pass `db_path` into `KnowledgeService(db_path=...)` or `get_connection(db_path=...)`.
- **In-Memory Testing**: Pass `":memory:"` for ephemeral, fast, non-persistent test suites.
- **Foreign Keys**: Enabled by default (`PRAGMA foreign_keys = ON;`).
- **Partial Unique Index**: `CREATE UNIQUE INDEX uq_km_approved ON knowledge_mappings(vendor, platform, normalized_command) WHERE approval_status = 'approved';` guarantees database-level duplicate prevention for approved knowledge.

---

## 10. How to Run Tests

From the `backend/` directory:

```bash
# Run knowledge isolated test suite (44 tests)
python -m pytest -v knowledge/tests

# Run compileall check
python -m compileall knowledge

# Run code style and linter checks
python -m flake8 knowledge
python -m black --check knowledge

# Run core backend test suite (133 tests)
python -m pytest -v tests
```

---

## 11. Known Limitations

1. **Exact Command Matching**: MVP implements exact normalized command lookup. Sub-mode / context-dependent regex matching is reserved for future integration.
2. **Single Approved Mapping per Command**: Only one mapping can be in `approved` status for any `(vendor, platform, normalized_command)` combination. Alternative interpretations must be managed via versioning or proposal revisions.
3. **Redaction Regex Scope**: Secret sanitization targets standard CLI credential patterns (passwords, secrets, keys, communities, tokens). Custom, proprietary inline secrets outside standard CLI conventions require explicit masking.
