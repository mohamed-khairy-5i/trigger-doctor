#!/usr/bin/env python3
"""trigger-doctor :: mechanical pre-flight for SKILL.md files.

Checks the facts a machine can verify (structure, limits, phrasing signals)
so the agent's judgment is spent only on the behavioral part (simulation).

Modes:
  skill   python3 parse_skill.py <SKILL.md path or skill directory>
  suite   python3 parse_skill.py <suite.json> --suite
  results python3 parse_skill.py <results.json> --results
  diff    python3 parse_skill.py <new.results.json> --diff <old.results.json>

Exit codes: 0 = clean (warnings allowed), 1 = usage/IO error,
2 = hard failures (or structurally invalid diff input),
3 = regression diff found flipped rows (diff mode only).
Stdlib only — no dependencies, runs anywhere the agent runs.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TOOL = "trigger-doctor.parse_skill/0.2.0"

DESC_LIMIT = 1024   # official Agent Skills description budget
NAME_LIMIT = 64     # official name budget
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
BODY_LIMIT = 500    # progressive-disclosure comfort ceiling

# Word-boundary patterns, not bare substrings: "that is" is a common English
# connective (not boundary language) and "triggers notifications" is not an
# imperative to the agent — substring matching produced false signals on both.
# Whitespace runs are \s+ so multi-space typos cannot defeat a phrase.
TRIGGER_PATTERNS = tuple(re.compile(p, re.IGNORECASE) for p in (
    r"\buse\s+this\s+skill\b",
    r"\buse\s+it\b",
    r"\buse\s+when\b",
    r"\buse\s+for\b",
    r"\btriggers?\s+when\b",
    r"\bwhenever\b",
    r"\b(activate|trigger)\s+(this|the)\s+skill\b",
))
BOUNDARY_PATTERNS = tuple(re.compile(p, re.IGNORECASE) for p in (
    r"\bdo not use\b",
    r"\bdon't use\b",
    r"\bnot (?:for|meant for|intended for)\b",
    r"\bavoid using\b",
    r"\binstead of\b",
    r"\boutside of\b",
    r"\bis the job of\b",
    r"\bonly (?:use|for)\b",
    r"\bout of scope\b",
    r"\bskip this\b",
    r"\breserved for\b",
    r"\bnot to be used\b",
    r"\bisn't for\b",
    r"\bis not for\b",
    r"\bshould not be\b",
))
# A mention whose line says the file is produced at runtime (save/write/create
# …) is not a shipped asset — flagging it as missing was a false alarm.
RUNTIME_OUTPUT_VERB = re.compile(
    r"\b(save|write|create|store|persist|export|record)\b", re.IGNORECASE)
# Security-relevant content signals. Warn-level pointers for the human/agent
# review — explicitly NOT a security audit and NOT a verdict on intent.
DANGER_SIGNALS = (
    ("credential path referenced",
     re.compile(r"\.aws[/\\]credentials|\.ssh[/\\]id_|(?:^|[/\\])id_rsa\b|\.netrc\b",
                re.IGNORECASE)),
    ("network call uploading a local file",
     # Data sourced from disk (@file, =@, -T/<path>, --post-file), NOT inline
     # literals: `curl -d '{"q": "x"}'` is a normal API example, while
     # `curl -d @~/.aws/credentials ...` is the classic exfil shape.
     re.compile(r"\b(?:curl|wget)\b[^\n]*(?:"
                r"--data(?:-binary|-raw|-urlencode)?\s*@|-d\s*@|"
                r"-(?:F|form)\s+[^\s]*=@|--form(?:-string)?\s+[^\s]*=@|"
                r"-(?:T|upload-file)\s+\S|--post-file(?:=|\s+\S))",
                re.IGNORECASE)),
    ("prompt-injection marker",
     re.compile(r"<!--\s*(?:SYSTEM|AI)\b|ignore (?:all )?previous instructions|"
                r"disregard (?:all )?(?:previous|above) instructions", re.IGNORECASE)),
)
FIRST_PERSON = re.compile(r"\b(i|i'm|i'll|i've|my|me|mine|we|our)\b", re.IGNORECASE)
# Single-quoted spans only count as quotes when not glued to a word char on
# either side — otherwise a contraction apostrophe (can't, user's) pairs with
# the NEXT quote and leaves quoted text unstripped, firing W04 falsely.
QUOTED = re.compile(r"\"[^\"]*\"|(?<![\w])'[^']*'(?![\w])")
LOCAL_REF = re.compile(
    r"\b((?:scripts|references|assets|suites)/[A-Za-z0-9_./-]+\.[A-Za-z0-9]+)"
)
PLACEHOLDER = re.compile(r"\b(TODO|TBD|FIXME|XXX)\b")


def _read_text(path: Path) -> tuple[str | None, dict]:
    """Read UTF-8 text (BOM tolerated). On decode/IO failure return a finding."""
    try:
        return path.read_text(encoding="utf-8-sig"), {}
    except UnicodeDecodeError:
        return None, {"id": "F00", "severity": "error",
                      "message": f"not valid UTF-8 text: {path}",
                      "fix": "SKILL.md and JSON inputs must be UTF-8 text files."}
    except OSError as exc:
        return None, {"id": "F00", "severity": "error",
                      "message": f"cannot read {path}: {exc}",
                      "fix": "Check the path and permissions."}


def _io_report(mode: str, path: Path, finding: dict) -> dict:
    return {"tool": TOOL, "mode": mode, "target": str(path), "ok": False,
            "io_error": True, "hard_failures": 1, "warnings": 0, "infos": 0,
            "stats": {}, "checks": [finding]}


def split_frontmatter(text: str):
    """Return (frontmatter_text, body_text); frontmatter None if absent."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i]), "\n".join(lines[i + 1:])
    return None, text


def _strip_inline_comment(value: str) -> str:
    """Strip a trailing ` # comment` from a plain scalar value.

    Quoted values keep everything up to their closing quote; unquoted values
    cut at the first space-before-hash, so phrases like `C# skills` survive.
    """
    if value[:1] in ('"', "'"):
        end = value.find(value[0], 1)
        if end != -1:
            return value[1:end]
    cut = value.find(" #")
    if cut != -1:
        value = value[:cut]
    return value.strip("\"'").strip()


def parse_fields(fm_text: str) -> dict:
    """Minimal YAML subset — deliberately not a YAML parser:

    - top-level `key: value` scalars (inline comments stripped, quotes removed)
    - block scalars: `>` folds with spaces, `|` preserves newlines
    - plain multi-line continuations fold with spaces
    - one level of nested mappings is kept as dotted `parent.child` keys
      (e.g. `metadata.author`) so indentation can never smear one field
      into another.
    """
    fields: dict = {}
    current = None
    block = None  # None | "folded" | "literal"
    for raw in fm_text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw[0] in " \t":
            if current is None:
                continue
            stripped = raw.strip()
            if block == "literal":
                fields[current] = (fields[current] + "\n" + stripped) \
                    if fields[current] else stripped
            elif block == "folded" or fields.get(current):
                fields[current] = (fields[current] + " " + stripped).strip()
            else:
                m2 = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", stripped)
                if m2 and m2.group(2).strip():
                    fields[f"{current}.{m2.group(1)}"] = \
                        _strip_inline_comment(m2.group(2).strip())
                else:
                    fields[current] = (fields[current] + " " + stripped).strip()
            continue
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", raw)
        if not m:
            current = None
            block = None
            continue
        current, value = m.group(1), m.group(2).strip()
        block = None
        if value in ("|", "|-", "|+"):
            fields[current] = ""  # block scalar: lines follow, newlines kept
            block = "literal"
        elif value in (">", ">-", ">+"):
            fields[current] = ""  # block scalar: lines follow, folded
            block = "folded"
        else:
            fields[current] = _strip_inline_comment(value)
    return fields


def strip_fenced_blocks(text: str) -> str:
    """Remove ``` fenced code blocks. References mentioned inside a fence are
    examples for the reader, not files the skill ships or calls — scanning
    them produced W06 false positives (e.g. `suites/your-skill.json` shown in
    an instruction snippet). Prose mentions are still scanned."""
    out: list = []
    inside = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            inside = not inside
            continue
        if not inside:
            out.append(line)
    return "\n".join(out)


def check_skill(path: Path) -> dict:
    findings: list = []

    def add(fid: str, sev: str, msg: str, fix: str = "") -> None:
        findings.append({"id": fid, "severity": sev, "message": msg, "fix": fix})

    text, io_err = _read_text(path)
    if text is None:
        return _io_report("skill", path, io_err)
    fm, body = split_frontmatter(text)
    fields = parse_fields(fm) if fm is not None else {}
    name = fields.get("name", "").strip()
    desc = fields.get("description", "").strip()
    body_lines = [ln for ln in body.splitlines() if ln.strip()]
    stats = {
        "name": name or None,
        "description_chars": len(desc),
        "description_limit": DESC_LIMIT,
        "body_lines": len(body_lines),
    }

    if fm is None:
        add("F01", "error",
            "No YAML frontmatter block (--- ... ---) found.",
            "Add frontmatter with `name` and `description`.")
    else:
        add("F01", "pass", "Frontmatter present.")

        if not name:
            add("F02", "error", "Missing `name` field.",
                "Add `name: lowercase-kebab`.")
        elif not NAME_RE.fullmatch(name):
            add("F02", "error",
                f"`name` `{name}` is not lowercase-kebab.",
                "Use only a-z, 0-9 and hyphens.")
        elif len(name) > NAME_LIMIT:
            add("F02", "error",
                f"`name` is {len(name)} chars (limit {NAME_LIMIT}).",
                "Shorten the name.")
        else:
            add("F02", "pass", f"name `{name}` ok.")

        if path.parent.name and name and path.parent.name != name:
            add("I01", "warn",
                f"Directory `{path.parent.name}` != skill name `{name}`.",
                "Rename the directory to match for packagers.")

        if not desc:
            add("F03", "error",
                "Missing `description` — the skill can never trigger.",
                "Write a description that says when to use it.")
        else:
            add("F03", "pass", "description present.")

            if len(desc) > DESC_LIMIT:
                add("F04", "error",
                    f"description is {len(desc)} chars — over the {DESC_LIMIT} "
                    "budget; agents may truncate it, cutting trigger cues.",
                    f"Trim to <= {DESC_LIMIT} chars.")
            else:
                add("F04", "pass",
                    f"description {len(desc)}/{DESC_LIMIT} chars.")

            if len(desc) < 40:
                add("W01", "warn",
                    "description under 40 chars — too vague to win the trigger gate.",
                    "Say concretely when to use it.")

            low = desc.lower()
            if not any(p.search(low) for p in TRIGGER_PATTERNS):
                add("W02", "warn",
                    "No imperative trigger phrase (e.g. `Use this skill when...`) "
                    "— reads as ad copy, not an instruction to the agent.",
                    "Add `Use this skill when...`.")

            if not any(p.search(low) for p in BOUNDARY_PATTERNS):
                add("I02", "info",
                    "No boundary line (when NOT to use it) — over-trigger risk "
                    "is unprotected.",
                    "Add one `Do not use for...` line.")

            bare = QUOTED.sub(" ", desc)
            if FIRST_PERSON.search(bare):
                add("W04", "warn",
                    "First-person wording — official style is a third-person "
                    "instruction to the agent.",
                    "Rewrite as `Use this skill when...`.")

    if len(body_lines) > BODY_LIMIT:
        add("W05", "warn",
            f"Body is {len(body_lines)} lines (> {BODY_LIMIT}) — move detail to "
            "references/ (progressive disclosure).",
            "Split into references/ files.")
    else:
        add("W05", "pass", f"body {len(body_lines)} lines (progressive disclosure ok).")

    prose = strip_fenced_blocks(text)
    missing, runtime = [], []
    for ref in sorted(set(LOCAL_REF.findall(prose))):
        if "<" in ref or ">" in ref:
            continue  # templated mention like suites/<skill-name>.json
        if (path.parent / ref).exists():
            continue
        line = next((ln for ln in prose.splitlines() if ref in ln), "")
        (runtime if RUNTIME_OUTPUT_VERB.search(line) else missing).append(ref)
    if missing:
        add("W06", "warn",
            "References files that do not exist: " + ", ".join(missing),
            "Create them or fix the paths.")
    else:
        add("W06", "pass", "All referenced local files exist.")
    if runtime:
        add("I04", "info",
            "Mentioned as created at runtime, not shipped: " + ", ".join(runtime),
            "No action needed — informational only.")

    if PLACEHOLDER.search(body):
        add("I03", "info", "Placeholder markers (TODO/TBD/FIXME) left in body.",
            "Resolve or remove them.")

    # Join backslash line-continuations first: real exfil commands are often
    # written across lines (`curl ... \` / `-d @secrets`), and a per-line scan
    # was deaf to that shape while catching benign inline examples.
    scan_text = re.sub(r"\\\n[ \t]*", " ", text)
    danger = [label for label, pat in DANGER_SIGNALS if pat.search(scan_text)]
    if danger:
        add("W07", "warn",
            "Security-relevant content signals (manual review required): "
            + "; ".join(danger),
            "Verify with the user that each is intentional — the pre-flight "
            "is not a security audit.")

    hard = [f for f in findings if f["severity"] == "error"]
    return {
        "tool": TOOL,
        "mode": "skill",
        "target": str(path),
        "ok": not hard,
        "hard_failures": len(hard),
        "warnings": sum(f["severity"] == "warn" for f in findings),
        "infos": sum(f["severity"] == "info" for f in findings),
        "stats": stats,
        "checks": findings,
    }


def check_suite(path: Path) -> dict:
    findings: list = []

    def add(fid: str, sev: str, msg: str, fix: str = "") -> None:
        findings.append({"id": fid, "severity": sev, "message": msg, "fix": fix})

    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except UnicodeDecodeError:
        return _io_report("suite", path,
                          {"id": "F00", "severity": "error",
                           "message": f"not valid UTF-8 text: {path}",
                           "fix": "JSON inputs must be UTF-8 text files."})
    except OSError as exc:
        return _io_report("suite", path,
                          {"id": "F00", "severity": "error",
                           "message": f"cannot read {path}: {exc}",
                           "fix": "Check the path and permissions."})
    except json.JSONDecodeError as exc:
        add("S00", "error", f"Invalid JSON: {exc}", "Fix the JSON syntax.")
        return {
            "tool": TOOL, "mode": "suite", "target": str(path), "ok": False,
            "hard_failures": 1, "warnings": 0, "infos": 0,
            "stats": {}, "checks": findings,
        }

    kind = None
    if isinstance(data, dict) and isinstance(data.get("cases"), list):
        cases = data["cases"]
        skill = data.get("skill")
        kind = data.get("kind")
    elif isinstance(data, list):
        cases = data
        skill = None
    else:
        add("S00", "error",
            "Suite must be a list of cases or an object with a `cases` list.",
            'Format: {"skill": str, "cases": [{"query": str, '
            '"should_trigger": true | false | "borderline"}]}')
        return {
            "tool": TOOL, "mode": "suite", "target": str(path), "ok": False,
            "hard_failures": 1, "warnings": 0, "infos": 0,
            "stats": {}, "checks": findings,
        }

    if not skill:
        add("S08", "info", "No `skill` label — name the skill this suite guards.",
            'Add "skill": "<skill-name>" at the top.')

    seen: set = set()
    for i, case in enumerate(cases, 1):
        if not isinstance(case, dict):
            add("S01", "error", f"case {i}: not an object.")
            continue
        q = case.get("query")
        s = case.get("should_trigger")
        if not isinstance(q, str) or not q.strip():
            add("S01", "error", f"case {i}: missing or blank `query`.")
        else:
            if len(q) > 500:
                add("S03", "warn", f"case {i}: query over 500 chars — keep utterances realistic.")
            key = " ".join(q.lower().split())
            if key in seen:
                add("S09", "warn", f"case {i}: duplicate query — duplicates pad the score.")
            seen.add(key)
        if isinstance(s, bool):
            pass
        elif s == "borderline":
            add("S10", "info",
                f"case {i}: `borderline` documents ambiguity — kept in the suite "
                "but asserts nothing (not scored as hit or miss).")
        else:
            add("S02", "error",
                f"case {i}: `should_trigger` must be true/false or \"borderline\".")

    n = len(cases)
    pos = sum(1 for c in cases if isinstance(c, dict) and c.get("should_trigger") is True)
    neg = sum(1 for c in cases if isinstance(c, dict) and c.get("should_trigger") is False)
    borderline = sum(1 for c in cases if isinstance(c, dict)
                     and c.get("should_trigger") == "borderline")

    if n < 4:
        add("S04", "error", f"Only {n} cases — too thin to say anything.")
    elif n < 12:
        add("S04", "warn", f"{n} cases — default suite is 12 (8 positive / 4 negative).")
    is_collision = kind == "collision"
    if pos < 3 and is_collision:
        add("S11", "info",
            "Collision suite: every row asserts a neighbor skill's job must "
            "NOT be grabbed — zero positive cases is the point.")
    elif pos < 3:
        add("S05", "error", f"Only {pos} positive cases — recall is untested.")
    if neg < 2:
        add("S06", "error",
            f"Only {neg} negative case{'s' if neg != 1 else ''} — "
            "over-triggering goes undetected."
            + (f" ({borderline} borderline rows are not counted as negatives.)"
               if borderline else ""))
    if pos and neg and pos < neg and not is_collision:
        add("S07", "warn", "More negatives than positives — the skill is being starved.")

    hard = [f for f in findings if f["severity"] == "error"]
    return {
        "tool": TOOL,
        "mode": "suite",
        "target": str(path),
        "ok": not hard,
        "hard_failures": len(hard),
        "warnings": sum(f["severity"] == "warn" for f in findings),
        "infos": sum(f["severity"] == "info" for f in findings),
        "stats": {"skill": skill, "kind": kind, "cases": n,
                  "positive": pos, "negative": neg, "borderline": borderline},
        "checks": findings,
    }


def _load_results(path: Path) -> tuple[dict | None, list]:
    """Load a Step-5 results file. Returns (data, findings); data None if unusable."""
    findings: list = []

    def add(fid: str, sev: str, msg: str, fix: str = "") -> None:
        findings.append({"id": fid, "severity": sev, "message": msg, "fix": fix})

    text, io_err = _read_text(path)
    if text is None:
        findings.append(io_err)
        return None, findings
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        add("R01", "error", f"Invalid JSON: {exc}", "Fix the JSON syntax.")
        return None, findings
    if not isinstance(data, dict) or not isinstance(data.get("cases"), list) \
            or not data["cases"]:
        add("R01", "error",
            "Results file must be an object with a non-empty `cases` list.",
            'Format: {"skill", "run", "agent", "cases": [{"query", "expected", '
            '"judged", "verdict"}], "score": {"hits", "misses", "borderline"}}')
        return None, findings
    return data, findings


def _validate_results_rows(data: dict, findings: list) -> tuple[dict, int]:
    """Append R02–R06 findings for every case row; return (counts, duplicates).

    Shared by --results and --diff so a structurally broken row can never be
    silently skipped by the comparison — the diff refuses to run on it.
    Strict booleans: JSON `1`/`0` are NOT true/false (suite mode rejects
    them too — same contract here).
    """
    def add(fid: str, sev: str, msg: str, fix: str = "") -> None:
        findings.append({"id": fid, "severity": sev, "message": msg, "fix": fix})

    for field in ("run", "agent"):
        if not str(data.get(field) or "").strip():
            add("R05", "warn",
                f"No `{field}` field — provenance of this run is unrecorded.",
                f'Add "{field}": "<{field}>" at the top.')

    counts = {"HIT": 0, "MISS": 0, "borderline": 0}
    seen: set = set()
    duplicates = 0
    for i, case in enumerate(data["cases"], 1):
        if not isinstance(case, dict):
            add("R02", "error", f"case {i}: not an object.")
            continue
        q, expected, judged, verdict = (case.get("query"), case.get("expected"),
                                        case.get("judged"), case.get("verdict"))
        if not isinstance(q, str) or not q.strip():
            add("R02", "error", f"case {i}: missing or blank `query`.")
        elif isinstance(expected, bool) or expected == "borderline":
            key = " ".join(q.lower().split())
            if key in seen:
                duplicates += 1
                add("R06", "warn",
                    f"case {i}: duplicate query — the first occurrence wins; "
                    "duplicates can hide a flipped row.",
                    "Keep one row per query.")
            seen.add(key)
        if expected is not True and expected is not False \
                and expected != "borderline":
            add("R02", "error",
                f"case {i}: `expected` must be true/false or \"borderline\" "
                f"(got {expected!r}) — JSON 1/0 are not booleans.")
        if not isinstance(judged, bool):
            add("R02", "error",
                f"case {i}: `judged` must be true or false (got {judged!r}).")
        if (expected is True or expected is False \
                or expected == "borderline") and isinstance(judged, bool):
            want = ("borderline" if expected == "borderline"
                    else ("HIT" if judged == expected else "MISS"))
            counts[want] += 1
            if verdict != want:
                add("R03", "error",
                    f"case {i}: verdict `{verdict}` inconsistent with "
                    f"expected={expected!r}, judged={judged!r} — should be `{want}`.",
                    "Verdict is mechanical: judged==expected → HIT, "
                    "else MISS, expected \"borderline\" → \"borderline\".")

    score = data.get("score")
    if not isinstance(score, dict):
        add("R04", "error", "Missing `score` object ({hits, misses, borderline}).")
    else:
        for key, want in (("hits", counts["HIT"]), ("misses", counts["MISS"]),
                          ("borderline", counts["borderline"])):
            got = score.get(key)
            if got != want:
                add("R04", "error",
                    f"score.{key} is {got!r} but cases contain {want} — "
                    "arithmetic mismatch.", "Recompute the score from the cases.")
    return counts, duplicates


def check_results(path: Path) -> dict:
    """Validate a results file: schema, verdict consistency, score arithmetic."""
    data, findings = _load_results(path)
    if data is None:
        first = findings[0]
        if first["id"] == "F00":
            return _io_report("results", path, first)
        return {"tool": TOOL, "mode": "results", "target": str(path), "ok": False,
                "hard_failures": 1, "warnings": 0, "infos": 0,
                "stats": {}, "checks": findings}

    counts, duplicates = _validate_results_rows(data, findings)
    hard = [f for f in findings if f["severity"] == "error"]
    return {
        "tool": TOOL, "mode": "results", "target": str(path),
        "ok": not hard, "hard_failures": len(hard),
        "warnings": sum(f["severity"] == "warn" for f in findings),
        "infos": sum(f["severity"] == "info" for f in findings),
        "stats": {"skill": data.get("skill"), "run": data.get("run"),
                  "cases": len(data["cases"]), "hits": counts["HIT"],
                  "misses": counts["MISS"], "borderline": counts["borderline"],
                  "duplicates": duplicates},
        "checks": findings,
    }


def diff_results(prev_path: Path, curr_path: Path) -> dict:
    """Regression diff: same query, same expectation, verdict flipped.

    Both inputs must pass FULL results validation first (shared row checks) —
    a malformed row, an int-as-bool, or a suite-shaped file is a structural
    error (exit 2), never a silent skip with a false "behavior identical".
    """
    prev, p_findings = _load_results(prev_path)
    curr, c_findings = _load_results(curr_path)
    p_counts = p_dups = c_counts = c_dups = None
    if prev is not None:
        p_counts, p_dups = _validate_results_rows(prev, p_findings)
    if curr is not None:
        c_counts, c_dups = _validate_results_rows(curr, c_findings)
    io_err = next((f for f in (p_findings + c_findings) if f["id"] == "F00"), None)
    if io_err is not None:
        broken = prev_path if prev is None else curr_path
        return {**_io_report("diff", broken, io_err), "against": str(prev_path)}
    if prev is None or curr is None or \
            any(f["severity"] == "error" for f in p_findings + c_findings):
        base = {"tool": TOOL, "mode": "diff", "target": str(curr_path),
                "against": str(prev_path), "ok": False, "hard_failures": 1,
                "warnings": 0, "infos": 0, "flips": [], "structural_error": True,
                "checks": (p_findings + c_findings) or
                          [{"id": "R01", "severity": "error",
                            "message": "unreadable diff input",
                            "fix": "Both inputs must be valid results files."}]}
        return base

    stats = {"prev_score": prev.get("score"), "curr_score": curr.get("score")}
    base = {"tool": TOOL, "mode": "diff", "target": str(curr_path),
            "against": str(prev_path), "stats": stats}

    def keyed(data):
        out = {}
        for case in data["cases"]:
            if isinstance(case, dict) and isinstance(case.get("query"), str):
                key = " ".join(case["query"].lower().split())
                out.setdefault(key, case)
        return out

    prev_map, curr_map = keyed(prev), keyed(curr)
    flips, expectation_changed = [], []
    for key, c in curr_map.items():
        p = prev_map.get(key)
        if p is None:
            continue
        exp_p, exp_c = p.get("expected"), c.get("expected")
        if exp_p != exp_c:
            expectation_changed.append({"query": c.get("query"),
                                        "prev": exp_p, "curr": exp_c})
            continue
        if exp_c == "borderline":
            continue  # borderline asserts nothing — no regression possible
        v_p, v_c = p.get("verdict"), c.get("verdict")
        if v_p in ("HIT", "MISS") and v_c in ("HIT", "MISS") and v_p != v_c:
            flips.append({"query": c.get("query"), "expected": exp_c,
                          "prev": {"judged": p.get("judged"), "verdict": v_p},
                          "curr": {"judged": c.get("judged"), "verdict": v_c}})
    added = [c.get("query") for k, c in curr_map.items() if k not in prev_map]
    removed = [p.get("query") for k, p in prev_map.items() if k not in curr_map]
    checks = []
    for f in flips:
        checks.append({"id": "D01", "severity": "error",
                       "message": f"flipped {f['prev']['verdict']} → {f['curr']['verdict']}"
                                  f" (expected={f['expected']!r}): {f['query']}",
                       "fix": "Re-check the skill change that altered this row."})
    checks.extend({"id": "D02", "severity": "info",
                   "message": f"expectation changed {e['prev']!r} → {e['curr']!r}: "
                              f"{e['query']} (suite edited — not scored as a flip)",
                   "fix": ""} for e in expectation_changed)
    if added:
        checks.append({"id": "D03", "severity": "info",
                       "message": f"{len(added)} new quer{'y' if len(added) == 1 else 'ies'} "
                                  f"vs previous run (coverage grew)", "fix": ""})
    if removed:
        checks.append({"id": "D04", "severity": "info",
                       "message": f"{len(removed)} quer{'y' if len(removed) == 1 else 'ies'} "
                                  "dropped vs previous run (coverage shrank)",
                       "fix": ""})
    total_dups = (p_dups or 0) + (c_dups or 0)
    if total_dups:
        checks.append({"id": "D05", "severity": "warn",
                       "message": f"{total_dups} duplicate query row(s) in the inputs — "
                                  "first occurrence used per query; a duplicate can "
                                  "hide a flip.",
                       "fix": "Keep one row per query and re-run."})
    if not flips and not expectation_changed and not added and not removed:
        checks.append({"id": "D00", "severity": "pass",
                       "message": "No flipped rows — behavior identical to previous run.",
                       "fix": ""})
    base.update({"ok": not flips, "hard_failures": len(flips),
                 "warnings": sum(c["severity"] == "warn" for c in checks),
                 "infos": sum(c["severity"] == "info" for c in checks),
                 "flips": flips, "expectation_changed": expectation_changed,
                 "added": added, "removed": removed, "checks": checks})
    return base


def main(argv=None) -> int:
    class _Parser(argparse.ArgumentParser):
        def error(self, message):  # usage errors exit 1; 2 is reserved for hard failures
            print(json.dumps({"tool": TOOL, "ok": False,
                              "error": f"usage: {message}"}))
            sys.exit(1)

    ap = _Parser(description="trigger-doctor mechanical pre-flight")
    ap.add_argument("target",
                    help="SKILL.md path, skill directory, suite .json (with --suite), "
                         "results .json (with --results, or as the NEW run with --diff)")
    ap.add_argument("--suite", action="store_true",
                    help="validate a trigger suite JSON instead of a skill")
    ap.add_argument("--results", action="store_true",
                    help="validate a Step-5 results file (schema + score arithmetic)")
    ap.add_argument("--diff", metavar="PREVIOUS_RESULTS",
                    help="regression diff: compare target (new results) against "
                         "the given previous results file")
    args = ap.parse_args(argv)
    if args.diff and (args.suite or args.results):
        ap.error("--diff cannot be combined with --suite or --results")
    if args.suite and args.results:
        ap.error("--suite and --results are mutually exclusive")

    path = Path(args.target)
    if not path.exists():
        print(json.dumps({"tool": TOOL, "ok": False,
                          "error": f"target not found: {path}"}))
        return 1
    if path.is_dir():
        if args.suite or args.results or args.diff:
            print(json.dumps({"tool": TOOL, "ok": False,
                              "error": f"this mode expects a JSON file, got a directory: {path}"}))
            return 1
        candidate = path / "SKILL.md"
        if not candidate.exists():
            print(json.dumps({"tool": TOOL, "ok": False,
                              "error": f"no SKILL.md in {path}"}))
            return 1
        path = candidate

    if args.diff:
        prev = Path(args.diff)
        if not prev.exists() or not prev.is_file():
            print(json.dumps({"tool": TOOL, "ok": False,
                              "error": f"previous results not found: {prev}"}))
            return 1
        report = diff_results(prev, path)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        if report.get("io_error"):  # unreadable/undecodable input
            return 1
        if report.get("structural_error"):  # could not compare at all
            return 2
        return 3 if report["flips"] else 0
    if args.results:
        report = check_results(path)
    else:
        report = check_suite(path) if args.suite else check_skill(path)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if report.get("io_error"):
        return 1
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
