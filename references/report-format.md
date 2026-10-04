# Report Format

The doctor's output shape. Users learn to trust a consistent report —
follow it exactly, every run.

```markdown
# 🩺 Trigger Report — <skill-name>

**Honesty label:** simulation of trigger judgment, not a runtime guarantee.

## Mechanical (scripts/parse_skill.py)
- Result: PASS / FAIL — X errors, Y warnings, Z infos
- Table of non-pass checks: id | severity | message
- (Full JSON available at <path or inline>)

## Simulation score
- Positives hit: X/8 — Negatives respected: Y/4 — Borderline: Z
- Verdict line: HEALTHY / NEEDS PRESCRIPTION / CRITICAL

## Per-query table
| # | query | expected | judged | verdict |
|---|-------|----------|--------|---------|
| 1 | ... | trigger | trigger | ✅ hit |
| 2 | ... | skip    | trigger | 🚫 grabbed |
| 3 | ... | trigger | skip    | ❌ missed |
| 4 | ... | either  | —       | ⚠️ borderline |

## Diagnosis
Per failure: query → named principle (P1–P8 from trigger-science.md) → root cause.

## Prescription
BEFORE (N chars):
```yaml
description: <old>
```
AFTER (M chars):
```yaml
description: <new>
```
Expected effect per failed row.

## Caveat
Simulated. For runtime proof, install the skill and try it live.

## Saved suite
suites/<skill-name>.json — re-run after every agent/model update.
```

Rules:

- Never skip the Honesty label or the Caveat.
- Every Diagnosis line must name a principle (P1–P8) — no vibes.
- The AFTER block must be copy-paste-ready YAML.
- If the suite existed before (regression run), add a `Regression diff`
  section listing rows whose verdict flipped.
