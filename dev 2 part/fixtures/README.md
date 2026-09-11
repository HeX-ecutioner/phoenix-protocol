# Teach the Auditor Fixtures

This directory contains synthetic test fixtures used to validate knowledge mapping persistence, normalization, duplicate prevention, and validation rules.

## Files

1. `sample_mappings.json`:
   - Valid synthetic command mappings covering four major network vendors:
     - **Cisco IOS** (`cisco_ios`)
     - **Juniper Junos** (`junos`)
     - **Fortinet FortiOS** (`fortios`)
     - **Palo Alto PAN-OS** (`panos`)
   - Covers various lifecycle states (`approved`, `proposed`).

2. `duplicate_mappings.json`:
   - Contains pairs of identical or whitespace/case-equivalent command patterns designed to verify duplicate detection and uniqueness constraints.

3. `invalid_mappings.json`:
   - Contains malformed payloads designed to trigger validation rejections (missing required fields, negative or excessive confidence values, invalid approval statuses, malformed rule IDs, excessive string lengths, secret-bearing patterns).

4. `vendor_mappings.json`:
   - Demonstrates the same conceptual security control (e.g. `remote_access_ssh_enforcement`) expressed across different vendor-specific syntaxes.
