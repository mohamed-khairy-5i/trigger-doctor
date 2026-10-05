# 🩺 Trigger Report — trigger-doctor (worked example)

> A **reproducible** demonstration: trigger-doctor's first patient was itself
> during the v0.1.0 self-test. The BEFORE state below is a **reconstruction**
> — the original pre-commit draft was never captured in git — rebuilt by
> removing the boundary sentence from the description (1002 − 122 = 880
> chars). Every command in this report can be re-run to reproduce its output.

**Honesty label:** simulation of trigger judgment, not a runtime guarantee.

## Mechanical (scripts/parse_skill.py)

BEFORE — description without the boundary line (reconstructed, 880 chars):

```
$ python3 scripts/parse_skill.py SKILL.md        # run inside the reconstructed copy
→ 1 finding: I02 (info): "No boundary line (when NOT to use it) —
  over-trigger risk is unprotected."
→ all hard checks green: frontmatter ✅ name ✅ description 880/1024 ✅
  body 74 lines ✅ references resolve ✅
```

AFTER — current `SKILL.md` (1002 chars):

```
$ python3 scripts/parse_skill.py SKILL.md
→ Result: PASS — 0 errors, 0 warnings, 0 infos
```

Reconstruction recipe: strip ` Do not use for ordinary code testing, CI
setup, or creating a brand-new skill from scratch — that is skill-creator's
job.` (122 chars) from the description, then re-run.

## Simulation score (suites/trigger-doctor.json — 12 cases)

- Positives hit: **8/8** — Negatives respected: **4/4** — Borderline: 1
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

AFTER (1002 chars) — one boundary line appended:
> Do not use for ordinary code testing, CI setup, or creating a brand-new
> skill from scratch — that is skill-creator's job.

Expected effect per row: 11 flips to `skip`; rows 1–8 unchanged; budget
still within the 1024 limit (880 → 1002).

## Caveat

Simulated. For runtime proof, install the skill and try it live.

## Saved suite

`suites/trigger-doctor.json` — re-run after every agent/model update and
diff flipped verdicts.
