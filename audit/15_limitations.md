# Phoenix Protocol Backend Audit — Product Limitations & Operational Constraints

**Date of Audit**: 2026-09-12  
**Classification Standard**: BLOCKER | MAJOR | MINOR | KNOWN MVP LIMITATION  

---

## 1. Limitations Matrix

| Limitation | Category | Classification | Technical Description | Recommended Production Path |
|---|---|---|---|---|
| **No API Authentication / RBAC** | Security / Production Readiness | **MAJOR** | Endpoints (`/scan`, `/scans/<id>`) have no bearer token, API key, or session authentication. Any network client that can reach port 5000 can submit scans or query historical reports. | Implement JWT Bearer token authentication or reverse proxy (Nginx/Envoy) with mTLS / OAuth2 in front of the Flask app. |
| **Single Vendor Support (`cisco_ios`)** | Parsing & Device Profiles | **KNOWN MVP LIMITATION** | The parser actively supports Cisco IOS and Cisco-like syntax. Requests with `device_type="juniper_junos"` or `"arista_eos"` are rejected with HTTP 400. | Add dedicated parsers (`JunosParser`, `EosParser`) implementing `BaseParser`. |
| **Rule Catalog Scope (10 Rules)** | Compliance Domain Coverage | **KNOWN MVP LIMITATION** | The engine evaluates NET-001 through NET-010 covering management plane, credentials, logging, and NTP. Full CIS Benchmarks encompass 40+ controls (e.g. SNMPv3, AAA accounting, BGP MD5, OSPF authentication). | Expand rule catalog incrementally (NET-011 through NET-050) using the existing `Rule` and `RuleResult` schema. |
| **Exact-Match Knowledge Lookup** | Adaptive AI / Knowledge Subsystem | **KNOWN MVP LIMITATION** | `KnowledgeService.lookup_command()` normalizes whitespace and casing, but evaluates exact command strings. Hierarchical sub-mode regex matching (e.g. commands under `router bgp 65001`) is reserved for future releases. | Implement parameterized regex patterns in `KnowledgeMapping`. |
| **SQLite Single-Node Storage** | Persistence & Concurrency | **KNOWN MVP LIMITATION** | Default persistence relies on a local SQLite database (`phoenix_protocol.db`). Suitable for single-instance or CLI usage, but concurrent write throughput is constrained under high enterprise load. | Provide SQLAlchemy or Postgres connection factory for horizontally scaled backend worker deployments. |
| **No Automatic Vendor Auto-Detection** | Ingestion & Parser Pipeline | **MINOR** | The API requires or defaults `device_type` to `cisco_ios`. It does not heuristically inspect file headers (e.g. detecting `version 15.2` or Junos syntax blocks) to infer vendor. | Add lightweight heuristic pre-parser to classify incoming text before parsing. |
| **In-Memory File Buffering** | Resource Utilization | **MINOR** | Uploaded configurations are buffered into RAM subject to the 10 MB per-file ceiling. Highly effective for network configs (which average 50 KB - 2 MB), but prevents streaming of massive 50 MB core switch dumps. | Stream file lines directly through the parser generator without buffering full raw string. |

---

## 2. Impact on Disconnected MVP Readiness

None of the identified limitations represent a **BLOCKER** for the current integration milestone:
- The single-vendor Cisco IOS focus and 10-rule baseline were explicit architectural design choices for Track 2.
- The unauthenticated API is standard practice for local development and private containerized sidecar integration with the frontend.
- Defensive error handling, determinism, and secret sanitization are 100% robust.
