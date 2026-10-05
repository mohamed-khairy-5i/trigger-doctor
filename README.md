<div align="center">
  <img src="assets/icon.png" width="160" alt="trigger-doctor icon — robot doctor with stethoscope"/>
  <h1>trigger-doctor</h1>
  <p>🩺 <b>Diagnose your agent skills</b> — behavioral testing, prescriptions &amp; regression suites</p>
  <p>
    <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-10b981"></a>&nbsp;
    <img alt="Supported agents: 79" src="https://img.shields.io/badge/agents-79-10b981">&nbsp;
    <img alt="Agent Skills open standard" src="https://img.shields.io/badge/Agent_Skills-open_standard-10b981">&nbsp;
    <img alt="Self-test: 12/12 passed" src="https://img.shields.io/badge/self--test-12%2F12-10b981">
  </p>
</div>

**Behavioral testing for skill triggers.** Most skills don't die of broken
logic — they die of never being opened. The `description` field is the gate
agents use to decide whether to load a skill, and almost nobody tests it.

trigger-doctor is an [Agent Skills](https://agentskills.io) skill that
diagnoses whether a skill will actually trigger, finds *why* it doesn't,
prescribes a fixed description, and saves a regression suite for the next
model update.

## Why it's different

| | Static linters (skill-doctor etc.) | **trigger-doctor** |
|---|---|---|
| Mechanical checks (limits, frontmatter) | ✅ | ✅ `scripts/parse_skill.py` |
| Behavioral test ("would it fire for *this* utterance?") | ❌ needs a live agent | ✅ the agent judges its own gate |
| Treatment | ❌ grades only | ✅ ready-to-paste rewritten description |
| Regression | ❌ | ✅ labeled suite saved in git, re-run after model updates |
| Scope | one platform | ✅ any [Agent Skills](https://agentskills.io) runtime (71+ agents via `npx skills add`) |

The behavioral layer is the moat: only a skill **inside** an agent can
simulate the agent's own trigger decision.

## The protocol

`SKILL.md` runs a 5-phase loop — **PARSE → SIMULATE → DIAGNOSE → PRESCRIBE → PERSIST**:

1. **PARSE** — `scripts/parse_skill.py` validates structure mechanically
   (frontmatter, 1024-char description budget, trigger/boundary phrasing,
   progressive disclosure, dangling references). Stdlib-only, exit code
   CI-friendly.
2. **SIMULATE** — a labeled suite (`{"query", "should_trigger"}` — the
   official eval format) is judged honestly against `name` + `description`
   only, with `borderline` allowed for simple tasks.
3. **DIAGNOSE** — every failure maps to a named principle
   (P1 Shy Description, P3 Vocabulary Gap, P6 No Boundary...) from
   `references/trigger-science.md`.
4. **PRESCRIBE** — a rewritten, copy-paste-ready description with
   BEFORE/AFTER character counts.
5. **PERSIST** — the suite is saved to `suites/<skill-name>.json`; future
   runs diff against it and flag flipped verdicts.

## Self-testing

The first patient is the doctor itself: `suites/trigger-doctor.json`
(12 cases) guards trigger-doctor's own description. Install it next to your
other skills and ask: *"check my skill"*.

## Install

**One command — 79 agents supported (open standard, no per-agent adapters):**

```bash
npx skills add mohamed-khairy-5i/trigger-doctor
```

The CLI knows each agent's directory — one SKILL.md, every agent:

| Agent | Lands in (global) |
|---|---|
| Claude Code | `~/.claude/skills/trigger-doctor/` |
| Hermes Agent | `~/.hermes/skills/trigger-doctor/` |
| Codex | `~/.codex/skills/trigger-doctor/` |
| Cursor | `~/.cursor/skills/trigger-doctor/` |
| Gemini CLI | `~/.gemini/skills/trigger-doctor/` |
| GitHub Copilot | `~/.copilot/skills/trigger-doctor/` |

Target only specific agents: `npx skills add mohamed-khairy-5i/trigger-doctor -a claude-code -a hermes-agent`.

**Manual:** copy this folder into your agent's skills directory.

**Docs:** the skill carries its own references (`references/trigger-science.md`,
`references/report-format.md`), and `examples/example-report.md` shows a real
worked report from the self-test — no external documentation site needed.

## Honesty rule

Reports are a **simulation** of trigger judgment, not a runtime guarantee.
Every report says so. For runtime proof, install the skill and try it live.

## License

MIT — see [LICENSE](LICENSE).
