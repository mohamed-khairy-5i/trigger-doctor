# 🩺 Trigger Report — trigger-doctor (worked example)

> This is a **real** report: trigger-doctor's first patient was itself,
> during the v0.1.0 self-test. Read it to see exactly what a run produces.

**Honesty label:** simulation of trigger judgment, not a runtime guarantee.

## Mechanical (scripts/parse_skill.py)

- Result: 1 finding caught → `I02` (info): *"No boundary line (when NOT to
  use it) — over-trigger risk is unprotected."*
- All hard checks green: frontmatter ✅ name ✅ description 880/1024 ✅
  body 74 lines ✅ references resolve ✅

## Simulation score (suites/trigger-doctor.json — 12 cases)

- Positives hit: **8/8** — Negatives respected: **4/4** — Borderline: 1
- Verdict: **NEEDS PRESCRIPTION** → applied → **HEALTHY**

## Per-query table

| # | query | expected | judged | verdict |
|---|-------|----------|--------|---------|
| 1 | I made a skill for my agent but it never activates, help me figure out why | trigger | trigger | ✅ hit |
| 2 | Can you check if this SKILL.md will actually fire when it should? | trigger | trigger | ✅ hit |
| 3 | My skill triggers on everything, it's so annoying - fix it | trigger | trigger | ✅ hit |
| 4 | Audit this skill description before I publish it | trigger | trigger | ✅ hit |
| 5 | here's my SKILL.md - will it trigger for 'summarize this pdf'? | trigger | trigger | ✅ hit (pasted file, no explanation) |
| 6 | write a regression suite for my skill's triggers before I update to the new model | trigger | trigger | ✅ hit |
| 7 | why isn't my skill working? | trigger | trigger | ✅ hit (quoted phrase) |
| 8 | improve my skill's description so it fires more reliably | trigger | trigger | ✅ hit |
| 9 | write unit tests for this Python function | skip | skip | ✅ respected |
| 10 | my pytest suite is failing, fix the import error | skip | skip | ✅ respected |
| 11 | create a brand-new skill from scratch that converts markdown to pdf | skip | borderline | ⚠️ risky pre-fix → respected post-fix |
| 12 | set up GitHub Actions CI to run my test suite | skip | skip | ✅ respected |

## Diagnosis

- Row 11 risk + `I02` finding map to principle **P6 — No Boundary**
  (`references/trigger-science.md`): the description claimed *when* to fire
  but never said *when not to*, leaving adjacent requests (creating a new
  skill — `skill-creator`'s lane) unprotected against hijacking.

## Prescription

BEFORE (880 chars) — ended at:
> ...Also use it proactively right after creating or editing any skill, and
> when reviewing third-party skills before installing them.

AFTER (1002 chars) — one boundary line appended:
> Do not use for ordinary code testing, CI setup, or creating a brand-new
> skill from scratch — that is skill-creator's job.

Expected effect per row: 11 un-ambiguated to `skip`; rows 1–8 unchanged;
budget still within the 1024 limit (880 → 1002).

## Caveat

Simulated. For runtime proof, install the skill and try it live.

## Saved suite

`suites/trigger-doctor.json` — re-run after every agent/model update and
diff flipped verdicts.
