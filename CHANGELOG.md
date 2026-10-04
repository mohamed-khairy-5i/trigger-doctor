# Changelog

All notable changes to trigger-doctor are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
