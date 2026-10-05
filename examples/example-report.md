# 🩺 Trigger Report — trigger-doctor (worked example)

> A **reproducible** demonstration: trigger-doctor's first patient was itself
> during the v0.1.0 self-test. The BEFORE state below is a **constructed
> demo**, not a historical record: it was made by removing the boundary
> sentence from the current description (1002 − 122 = 880 chars). No claim
> is made about any earlier version of this file. Every command re-runs to
> reproduce its output.

**Honesty label:** simulation of trigger judgment, not a runtime guarantee.

## Mechanical (scripts/parse_skill.py)

BEFORE — description without the boundary line (reconstructed, 880 chars):

```
$ python3 scripts/parse_skill.py SKILL.md        # run inside the reconstructed copy
→ 1 finding: I02 (info): "No boundary line (when NOT to use it) —
  over-trigger risk is unprotected."
→ all hard checks green: frontmatter ✅ name ✅ description 880/1024 ✅
  body within the progressive-disclosure budget ✅ references resolve ✅
```

AFTER — current `SKILL.md` (1002 chars):

```
$ python3 scripts/parse_skill.py SKILL.md
→ Result: PASS — 0 errors, 0 warnings, 0 infos
```

Demo recipe: strip ` Do not use for ordinary code testing, CI
setup, or creating a brand-new skill from scratch — that is skill-creator's
job.` (122 chars) from the description, then re-run.

## Simulation score (suites/trigger-doctor.json — 12 cases)

- Positives hit: **8/8** — Negatives respected: **4/4** — Borderline
  judged: 1 (row 11, BEFORE state only; the shipped 12-case suite is
  8 positive / 4 negative with no borderline rows)
- Verdict against the BEFORE state: **NEEDS PRESCRIPTION** → applied → **HEALTHY**

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
  (`references/trigger-science.md`): the BEFORE description claimed *when*
  to fire but never said *when not to*, leaving adjacent requests (creating
  a new skill — `skill-creator`'s lane) unprotected against hijacking.

## Prescription

BEFORE (880 chars, reconstructed) — ended at:
> ...Also use it proactively right after creating or editing any skill, and
> when reviewing third-party skills before installing them.

AFTER (1002 chars) — one boundary line appended (copy-paste-ready):

```yaml
---
name: trigger-doctor
description: Diagnose and repair agent-skill triggering. Use this skill whenever a user wants to check whether a skill will actually activate, complains that a skill never fires or fires too often, asks to test, audit, or improve a SKILL.md description, or wants a regression suite saved before a model or agent update — even if they just say "check my skill", "why isn't my skill working", "make my skill trigger", or paste a SKILL.md without explaining why. It runs deterministic validation, simulates labeled user queries against the description, diagnoses under- and over-triggering against the official Agent Skills description science, prescribes a rewritten ready-to-paste description, and persists an eval suite for re-testing after agent or model updates. Also use it proactively right after creating or editing any skill, and when reviewing third-party skills before installing them. Do not use for ordinary code testing, CI setup, or creating a brand-new skill from scratch — that is skill-creator's job.
---
```

Expected effect per row: 11 flips to `skip`; rows 1–8 unchanged; budget
still within the 1024 limit (880 → 1002).

## Caveat

Simulated. For runtime proof, install the skill and try it live.

## Saved files

- `suites/trigger-doctor.json` — baseline (expectations only); never
  overwritten.
- `suites/trigger-doctor.results.json` — the latest run's judged verdicts
  (same schema as the report score), with
  `suites/trigger-doctor.previous.results.json` snapshotted before each
  re-run so `--diff` always has a comparison source.

Re-run after every agent/model update — `--diff` exits `3` the moment a
verdict flips.
