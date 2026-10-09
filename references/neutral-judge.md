# Neutral Judge Protocol

Why this exists: the doctor's behavioral layer is judged by the agent
running the protocol — the same kind of agent whose gate is being tested.
Self-judging has a conflict of interest. A **neutral judge** is a second,
independent agent (different model, or a fresh session with zero doctor
context) that reads the target blind and answers the same question.

Two simulated opinions do not equal runtime truth — the honesty label
still applies. What the cross-check buys you is a *bias detector*: if two
independent judges disagree on a row, the description is ambiguous, and
ambiguity is a prescription target (P1/P2/P3, P6).

## The blind protocol

1. **Build the blind pack.** From the target's `SKILL.md` and baseline
   suite, prepare:
   - `name` (verbatim)
   - `description` (verbatim)
   - the suite's `query` strings, shuffled, **without** their
     `should_trigger` labels — the judge must not see expectations.
2. **Brief the judge** (a second agent/model, unrelated session):

   > Loading only this name + description: for each utterance below,
   > would you open this skill? Answer each with exactly one word —
   > `trigger`, `skip`, or `borderline`. Judge every row independently.

3. **Convert the answers** to a results file in the standard schema —
   `expected` copied from the baseline suite, `judged` from the judge,
   verdicts `HIT`/`MISS`/`borderline`, and a computed `score`.
4. **Validate mechanically** (catches malformed rows and lying scores):
   ```bash
   python3 scripts/parse_skill.py judge.results.json --results
   ```
5. **Diff the two judges** (primary results vs neutral results):
   ```bash
   python3 scripts/parse_skill.py judge.results.json --diff primary.results.json
   ```
   Exit `0` = both judges agree on every row. Exit `3` = flipped rows,
   named in the output — those rows are your data.

## Reading the disagreement

| Flipped rows | Reading | Action |
|---|---|---|
| 0–1 | description is neutral — robust to who reads it | ship it |
| 2–3 | ambiguous phrasing on those rows | revise, re-run the cross-check |
| 4+ | description leans on judge-specific context | rewrite for neutrality (P2: say *when*, not *how*) |

Also give the judge the **collision suite** (`suites/<skill>.json`
sibling with `"kind": "collision"`): any `trigger` answer on a collision
row is a Misroute signal (P6/P7/P8) even if the primary judge respected
it — two judges missing the same boundary is how hijacks slip through.

## Rules

- The judge never sees the diagnosis, the science, or the expectations.
- Never let the primary judge "fix" the neutral judge's answers — the
  disagreement IS the result.
- Record the judge's model name in the Patient card; an unnamed judge is
  an anecdote.
