# Changelog

All notable changes to trigger-doctor are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.3] - 2026-10-05

### Fixed
- **W07 network signal retuned in both directions** (external-review finding):
  it fired on inline-literal API examples (`curl -d '{"q": "x"}'` — a normal
  documentation shape) while staying silent on multi-line exfil written with
  backslash continuations — the most common real-world layout. Now the scan
  joins continuations before matching and fires only on **file-sourced**
  uploads (`-d @file`, `-F name=@file`, `-T path`, `--post-file`), the actual
  exfil shape. 0 fires on the 69-skill local corpus, exfil fixtures caught in
  both layouts.

### Added
- **Mechanical regression diff**: `--results` validates a results file
  (schema, verdict consistency, score arithmetic — R01–R05) and `--diff
  <previous>` flags flipped verdict rows (D01) as data, not agent memory.
  Exit contract: 0 clean / 1 usage / 2 hard or broken diff input / 3 flipped
  rows found.
- CI: three new steps — W07 two-direction contract (multi-line exfil caught,
  inline example silent), results-file validation with score-mismatch
  negative control, and the full diff contract (identical → 0, flip → 3,
  broken → 2, flip rows named).

## [0.1.2] - 2026-10-05

### Fixed
- **PERSIST split into two files**: the baseline suite (expectations, never
  overwritten without explicit user go-ahead) and
  `suites/<skill-name>.results.json` (judged verdicts, written every run) —
  the regression diff finally has a data source instead of "overwrite
  baseline" + "diff against previous" contradicting each other.
- **Path-traversal hardening**: Step 5 filename guard — the target's `name`
  is used for filenames only if it passes the lowercase-kebab check (F02);
  `..`, drive letters, and absolute paths are refused (write inside the
  skill's own `suites/` only).
- `S06` no longer silently punishes replaced negatives: the message now
  notes how many borderline rows are excluded from the negative count.
- `example-report.md`: the BEFORE state is framed purely as a **constructed
  demo** — no residual claim about unrecorded history.
- README: the "behavioral layer is the moat" line replaced with an honest
  framing — simulation chosen for cost (10–100× cheaper), not a claim to
  runtime truth.

### Added
- `W07` danger-signal scan (warn-level; the pre-flight is explicitly **not**
  a security audit): credential paths (`.aws/credentials`, `.ssh/id_*`,
  `id_rsa`, `.netrc`), network calls that upload data (`curl`/`wget` with
  `-d`/`-F`/`-T`/`--post-*`), and prompt-injection markers
  (`<!-- SYSTEM -->`, "ignore previous instructions").
- SKILL.md Step 1: `py` Windows command in the same code block (closes the
  `python3` half-fix) and the not-a-security-scanner scope note.
- `.gitattributes` — LF everywhere, images binary (no CRLF churn).
- Git tags: `v0.1.1` (back-tagged to the audit-fix commit) and `v0.1.2`.

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
