# Phoenix Protocol Backend Audit — Scoring Engine Verification

**Date of Audit**: 2026-09-12  
**Service Endpoint Audited**: `POST /scan`  
**Scoring Implementation**: `backend/app/services/compliance.py`  

---

## 1. Compliance Score Formula & Invariants

The backend specifies the following deterministic scoring formula:

$$\text{Compliance Score} = \text{round}\left( \frac{\text{passed\_rules}}{\text{passed\_rules} + \text{failed\_rules}} \times 100, 2 \right)$$

### Strict Mathematical Invariants:
1. **Denominator Isolation**: Only rules with unambiguous `pass` or `fail` verdicts contribute to the tested denominator. Rules resulting in `warning`, `not_applicable`, or `error` are counted in summary statistics but **strictly excluded** from the tested-rule denominator.
2. **Zero Tested Rules**: If $\text{passed} + \text{failed} = 0$, the engine returns `0.0%` (guards against division by zero).
3. **Multi-Device Aggregation**: Scan-level compliance is calculated across the total aggregate pool of rule evaluations, **never** by averaging the individual percentage scores of devices.

---

## 2. Empirical Verification from Live Black-Box Runs

All data below is extracted from actual responses in [`audit/api_responses/`](api_responses/).

| Test Case | Response Artifact | Passed | Failed | Warning | Error | Total | Raw Tested Formula | Actual API Score | Result |
|---|---|---|---|---|---|---|---|---|---|
| **Fully Compliant** | `compliant.json` | 10 | 0 | 0 | 0 | 10 | $\frac{10}{10+0} \times 100$ | **100.0%** | **EXACT MATCH** |
| **Fully Failing** | `failing.json` | 0 | 10 | 0 | 0 | 10 | $\frac{0}{0+10} \times 100$ | **0.0%** | **EXACT MATCH** |
| **Ambiguous Config** | `ambiguous.json` | 1 | 5 | 4 | 0 | 10 | $\frac{1}{1+5} \times 100 = 16.666\dots$ | **16.67%** | **EXACT MATCH** |
| **Partial Config** | `path_traversal.json` | 2 | 5 | 3 | 0 | 10 | $\frac{2}{2+5} \times 100 = 28.571\dots$ | **28.57%** | **EXACT MATCH** |
| **Secondary Device** | `multi_device_secondary.json`| 7 | 3 | 0 | 0 | 10 | $\frac{7}{7+3} \times 100$ | **70.0%** | **EXACT MATCH** |

---

## 3. Multi-Device Aggregation Audit

Audited from [`audit/api_responses/multi_device.json`](api_responses/multi_device.json) which uploaded three devices in a single scan:

### Per-Device Statistics:
- **Device 1 (`CORE-RTR-01`)**: 10 Passed, 0 Failed, 0 Warning $\rightarrow$ **100.0%**
- **Device 2 (`DEFAULT-RTR`)**: 0 Passed, 10 Failed, 0 Warning $\rightarrow$ **0.0%**
- **Device 3 (`SEC-DIST-01`)**: 7 Passed, 3 Failed, 0 Warning $\rightarrow$ **70.0%**

### Aggregate Calculation:
- $\text{Aggregate Passed} = 10 + 0 + 7 = 17$
- $\text{Aggregate Failed} = 0 + 10 + 3 = 13$
- $\text{Aggregate Tested} = 17 + 13 = 30$
- $\text{Scan-Level Compliance Score} = \frac{17}{30} \times 100 = 56.666\dots \rightarrow \mathbf{56.67\%}$

**API Response Verified**:
```json
{
  "compliance_score": 56.67,
  "summary": {
    "passed_rules": 17,
    "failed_rules": 13,
    "warning_rules": 0,
    "total_rules": 30,
    "tested_rule_compliance": 56.67
  }
}
```

---

## 4. Verdict

**PASS** — The scoring algorithm complies with all design specifications. Formula implementation is mathematically consistent, correctly excludes warnings from the denominator, and aggregates multi-device batches by summing individual rule outcomes rather than averaging device percentages.
