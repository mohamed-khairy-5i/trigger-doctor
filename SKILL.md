---
name: trigger-doctor
description: Diagnose and repair agent-skill triggering. Use this skill whenever a user wants to check whether a skill will actually activate, complains that a skill never fires or fires too often, asks to test, audit, or improve a SKILL.md description, or wants a regression suite saved before a model or agent update — even if they just say "check my skill", "why isn't my skill working", "make my skill trigger", or paste a SKILL.md without explaining why. It runs deterministic validation, simulates labeled user queries against the description, diagnoses under- and over-triggering against the official Agent Skills description science, prescribes a rewritten ready-to-paste description, and persists an eval suite for re-testing after agent or model updates. Also use it proactively right after creating or editing any skill, and when reviewing third-party skills before installing them. Do not use for ordinary code testing, CI setup, or creating a brand-new skill from scratch — that is skill-creator's job.
---

# Trigger Doctor

Diagnose whether an agent skill will actually **trigger**, diagnose why it
doesn't, prescribe a fixed description, and persist a regression suite.

The description field carries the entire burden of skill activation: agents
load only `name` + `description` at startup and decide from that alone whether
to read the skill. Most broken skills are not broken inside — they are never
opened. This skill closes that gap.

**Honesty rule (never violate):** results are a *simulation* of triggering
judgment, not a runtime guarantee. Always label reports as simulated. If the
user needs runtime proof, tell them to install the skill and try it live.

## Workflow

### Step 0 — Gather the target

Ask for (or detect) one of:

- a path to a skill directory containing `SKILL.md`, or
- pasted SKILL.md content, or
- the name of an installed skill to locate.

Also ask for a target agent/runtime only if the user says triggering differs
per agent; the protocol is runtime-agnostic by default.

### Step 1 — PARSE (deterministic)

Run:

```bash
python3 scripts/parse_skill.py <path-to-SKILL.md>
```

Run from this skill's own directory so the relative `scripts/` path resolves.
On Windows there is no `python3` — use the launcher instead:
`py scripts\parse_skill.py <path-to-SKILL.md>`.

The script validates mechanical facts (frontmatter, limits, description
qualities) and exits `2` on hard failures (`1` on usage/IO errors). Treat its
JSON findings as ground truth for structure. If it reports hard failures, fix
those with the user before continuing — a skill that fails parsing will
misbehave in ways no simulation can fix.

### Step 2 — SIMULATE (behavioral)

Build a labeled query suite in the official eval format
(`[{"query": str, "should_trigger": bool}]`):

- Default: **12 queries — 8 positive, 4 negative** (see ratios and quality
  rules in `references/trigger-science.md`).
- If `suites/<skill-name>.json` already exists, use it (this is a regression
  run) and say so.
- Positives must paraphrase real user intent **including utterances that never
  name the skill's domain**.
- Negatives must be adjacent-but-out-of-scope tasks the skill must NOT grab.

Then judge each query honestly: *loading only the target's `name` +
`description` into mind — would you open this skill for this utterance?*
Apply the official nuance: simple one-step tasks that basic tools already
handle tend not to trigger any skill; mark such rows `borderline` rather than
forcing a verdict. The suite validator accepts `"borderline"` and counts it
(S10) without scoring it as a hit or a miss.

### Step 3 — DIAGNOSE

For every failure (missed positive = under-trigger, grabbed negative =
over-trigger), map the cause to a named principle in
`references/trigger-science.md` (e.g. not pushy enough, implementation-speak
instead of user intent, missing boundary, exceeds limits). Never diagnose
without naming the principle.

### Step 4 — PRESCRIBE

Rewrite the `description` applying the science:

1. Imperative phrasing ("Use this skill when...").
2. User intent, not implementation.
3. Pushy: explicitly include contexts where the user doesn't name the domain.
4. Boundaries: one line of when NOT to use it (protects against over-trigger).
5. Hard limit: **1024 characters** — verify after rewriting.

Present BEFORE/AFTER with character counts and the expected direction of
change per failed row. Provide the new description in a copy-paste-ready
block.

### Step 5 — PERSIST (regression)

Save the suite to `suites/<skill-name>.json` (overwrite baseline) and print
the report per `references/report-format.md`. On any future re-run, diff
against the previous suite results and flag rows that flipped.

## Report

Follow `references/report-format.md` exactly — users learn to trust a
consistent shape. Minimum sections: Mechanical, Simulation score, per-query
table, Diagnosis (with principle names), Prescription (BEFORE/AFTER), Caveat,
Saved suite path.

## Scope

- One skill per run. If given many, run the protocol per skill and summarize.
- Do not modify the target skill's files other than proposing the new
  description; applying it is the user's choice.
- For creating skills from scratch, that is `skill-creator`'s job — this skill
  is the doctor, not the midwife.
