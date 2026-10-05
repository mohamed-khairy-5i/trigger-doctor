# Changelog

All notable changes to trigger-doctor are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.1] - 2026-10-05

### Fixed
- `examples/example-report.md` rebuilt as a reproducible worked example: the
  BEFORE state is now labeled a **reconstruction** (1002 − 122 = 880 chars)
  instead of an unverifiable "real report" claim; all outputs re-captured
  from live runs with reproduction commands included.
- Suite validator contradiction resolved: `should_trigger: "borderline"` is
  now accepted and counted (new `S10` info, reported in stats) instead of
  failing `S02` — matching the SKILL.md Step 2 instruction to mark borderline
  rows rather than force a verdict.
- Phrase detection switched from bare substrings to word-boundary patterns:
  "that is" no longer passes as boundary language, and a bare "triggers" no
  longer passes as an imperative to the agent.
- `W06` no longer flags files mentioned as runtime outputs ("save findings to
  references/…") — now informational `I04`; genuinely broken references still
  warn.
- Usage errors exit `1` with a JSON error payload, reserving exit `2` for
  hard failures exactly as the documented contract states.

### Added
- GitHub Actions CI (`.github/workflows/ci.yml`): mechanical self pre-flight,
  suite validation, borderline acceptance, broken-skill negative control, and
  exit-code contract checks; CI badge added to README.
- Windows guidance in SKILL.md Step 1: use the `py` launcher (`python3` does
  not exist on Windows); run from the skill's own directory.

### Removed
- Dead assets `assets/banner.png` (1.6 MB) and `assets/icon-dark.png`
  (331 KB) — unreferenced anywhere in the repo; recoverable from git history.

## [0.1.0] - 2026-10-04

### Added
- 5-phase protocol in `SKILL.md`: PARSE → SIMULATE → DIAGNOSE → PRESCRIBE → PERSIST.
- `scripts/parse_skill.py` — stdlib-only mechanical pre-flight (frontmatter,
  1024-char description budget, trigger/boundary phrasing, progressive
  disclosure, dangling references) with CI-friendly exit codes; `--suite`
  mode validates the official `{"query", "should_trigger"}` eval format.
- `references/trigger-science.md` — named failure taxonomy P1–P8
  (under-trigger / over-trigger) distilled from the official Agent Skills
  documentation, `skill-creator`, and `writing-skills`.
- `references/report-format.md` — consistent report shape with a mandatory
  honesty label (simulation ≠ runtime guarantee).
- `suites/trigger-doctor.json` — 12-case self-test suite (8 positive /
  4 negative); the doctor's first patient is itself.
- Regression workflow: suites are saved in git and diffed after agent or
  model updates.
