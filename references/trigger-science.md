# Trigger Science

The distilled rules that decide whether a skill ever gets opened.
Distilled from the official Agent Skills specification (agentskills.io),
Anthropic's `skill-creator`, obra/superpowers `writing-skills`, and
Anthropic's best-practices engineering notes — the sources that define
how the ecosystem expects descriptions to behave.

## 1. The gate

An agent starts a session with only `name` + `description` for every
installed skill. The body of the skill is loaded **on demand**, after the
agent decides the description matches the current task. So the description
is not documentation — it is a **gate**. If it loses at the gate, the rest
of the skill is unread literature.

## 2. The 1024 budget

The official hard limit for `description` is **1024 characters**. Agents may
truncate or summarize beyond that. Treat it like a payload budget: front-load
the trigger cues; never spend the budget on history or philosophy.

## 3. Pushiness (the under-trigger killer)

The most common death is **never firing**. Real users don't announce the
domain: they say *"why isn't my thing working"*, *"check this before I
publish"*. A winning description explicitly claims those utterances:

- imperative voice: `Use this skill when...`
- quoted real phrases: `...even if they just say "check my skill"`
- proactive claim: `Also use it proactively right after creating or editing any skill.`

## 4. Intent, not implementation

Users speak outcomes; weak descriptions speak mechanics.
❌ `Parses frontmatter YAML and validates field lengths.`
✅ `Use when a skill never activates, or you're about to publish one.`
Mechanics belong in the body. The description sells **when**, not **how**.

## 5. The simple-task exemption

Official guidance: simple one-step tasks that base tools already handle
tend **not** to trigger any skill. A good suite marks such rows
`borderline` instead of forcing a verdict — and a good description does
not grab them.

## 6. Boundaries protect

One line of `Do not use for...` prevents over-triggering (the skill
hijacking conversations it shouldn't) and keeps adjacent tools
(`skill-creator`, plain code testing) in their lanes. Under-trigger is
fixed by pushiness; over-trigger is fixed by boundaries.

## 7. Third person, imperative

The description is an instruction **to the agent**, not ad copy to a human.
Official style is third-person imperative: `Use this skill when...`.
First-person ("I will help you...") wastes budget and misframes the gate.

## 8. Failure taxonomy

Name the disease before prescribing. Every simulation failure maps to one:

| Class | ID | Name | Symptom | Fix |
|---|---|---|---|---|
| under | P1 | Shy Description | misses utterances that name the domain | add `Use this skill when...` |
| under | P2 | Implementation-Speak | describes how, not when | rewrite as user intent |
| under | P3 | Vocabulary Gap | user's words never appear ("not working") | quote real user phrases |
| under | P4 | Implicit Domain | misses utterances that never name the domain | claim domain-less phrasings |
| under | P5 | Budget Cut | cues truncated past 1024 | front-load, trim |
| over | P6 | No Boundary | grabs adjacent tasks | add `Do not use for...` |
| over | P7 | Broad Nouns | generic "test/check/improve" unqualified | qualify every noun |
| over | P8 | Hijack Risk | competes with built-in tools for simple tasks | respect the simple-task exemption |

## 9. Prescription recipe (PRESCRIBE checklist)

1. First sentence: what it does, one line.
2. `Use this skill when...` + 3–6 concrete cues (include 1–2 quoted user phrases).
3. One boundary line: `Do not use for...`.
4. Proactive claim if the skill should run unasked.
5. Verify ≤ 1024 chars. Re-simulate the suite against the new text.

## 10. Suites are memory (regression)

Model and agent updates silently change trigger behavior. A labeled suite
(`[{"query": str, "should_trigger": bool}]`) saved in git is the only cheap
defense: re-run it after every update and diff the verdicts. This is the
official eval format — trigger-doctor adds nothing proprietary to it.
Default: **12 cases — 8 positive, 4 negative**; negatives are half the medicine.
