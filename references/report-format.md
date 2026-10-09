# Report Format

The doctor's output shape. Users learn to trust a consistent report —
follow it exactly, every run.

```markdown
# 🩺 Trigger Report — <skill-name>

**Honesty label:** simulation of trigger judgment, not a runtime guarantee.

## Patient card
- Tool: trigger-doctor.parse_skill/<version> · Judge: <agent/model name>
- Date: <YYYY-MM-DD> · Suite: <name>.json (<N> cases)
- Target: <path> · description_chars: <N>/1024

## Mechanical (scripts/parse_skill.py)
- Result: PASS / FAIL — X errors, Y warnings, Z infos
- Table of non-pass checks: id | severity | message
- (Full JSON available at <path or inline>)

## Simulation score
- Positives hit: X/8 — Negatives respected: Y/4 — Borderline: Z
- Consistency: judged R rounds — weakest row agreed <x>/R
  (rows under 8/10 are UNSTABLE — flag them, never average them away)
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

## Saved files
- `suites/<skill-name>.json` — baseline (expectations only); never overwritten.
- `suites/<skill-name>.results.json` — this run's judged verdicts; the
  regression diff compares it against the previous results file.
- `suites/<skill-name>.collision.json` — optional neighbor-domain suite
  (all `should_trigger: false`); a grabbed row there is a Misroute
  (P6/P7/P8) even when the main suite is green.
```

Rules:

- Never skip the Honesty label, the Patient card, or the Caveat.
- The Patient card records tool version, judge (agent/model), date and
  suite — a report without provenance is an anecdote, not a result.
- The Consistency line is mandatory whenever the suite was judged more
  than once (see SKILL.md Step 2); for single-round quick checks write
  `Consistency: single round — no stability data`.
- For a neutral-judge cross-check (references/neutral-judge.md), add a
  `Neutral judge` section: judge name, its score, and the flipped rows
  from `--diff` between the two results files.
- Every Diagnosis line must name a principle (P1–P8) — no vibes.
- The AFTER block must be copy-paste-ready YAML.
- If the suite existed before (regression run), add a `Regression diff`
  section listing rows whose verdict flipped — run the mechanical diff
  (`parse_skill.py <new>.results.json --diff <old>.results.json`; exit `3`
  means flips) and name the rows it reports, never diff against the baseline
  (expectations do not carry verdicts).
