#!/usr/bin/env python3
"""trigger-doctor :: mechanical pre-flight for SKILL.md files.

Checks the facts a machine can verify (structure, limits, phrasing signals)
so the agent's judgment is spent only on the behavioral part (simulation).

Modes:
  skill   python3 parse_skill.py <SKILL.md path or skill directory>
  suite   python3 parse_skill.py <suite.json> --suite

Exit codes: 0 = clean (warnings allowed), 1 = usage/IO error, 2 = hard failures.
Stdlib only — no dependencies, runs anywhere the agent runs.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TOOL = "trigger-doctor.parse_skill/0.1"

DESC_LIMIT = 1024   # official Agent Skills description budget
NAME_LIMIT = 64     # official name budget
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
BODY_LIMIT = 500    # progressive-disclosure comfort ceiling

# Word-boundary patterns, not bare substrings: "that is" is a common English
# connective (not boundary language) and "triggers notifications" is not an
# imperative to the agent — substring matching produced false signals on both.
TRIGGER_PATTERNS = tuple(re.compile(p, re.IGNORECASE) for p in (
    r"\buse this skill\b",
    r"\buse it\b",
    r"\buse when\b",
    r"\buse for\b",
    r"\bwhenever\b",
    r"\b(activate|trigger) (this|the) skill\b",
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
))
# A mention whose line says the file is produced at runtime (save/write/create
# …) is not a shipped asset — flagging it as missing was a false alarm.
RUNTIME_OUTPUT_VERB = re.compile(
    r"\b(save|write|create|store|persist|export|record)\b", re.IGNORECASE)
FIRST_PERSON = re.compile(r"\b(i|i'm|i'll|i've|my|me|mine|we|our)\b", re.IGNORECASE)
QUOTED = re.compile(r"\"[^\"]*\"|'[^']*'")
LOCAL_REF = re.compile(
    r"\b((?:scripts|references|assets|suites)/[A-Za-z0-9_./-]+\.[A-Za-z0-9]+)"
)
PLACEHOLDER = re.compile(r"\b(TODO|TBD|FIXME|XXX)\b")


def split_frontmatter(text: str):
    """Return (frontmatter_text, body_text); frontmatter None if absent."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i]), "\n".join(lines[i + 1:])
    return None, text


def parse_fields(fm_text: str) -> dict:
    """Minimal YAML subset: top-level `key: value` plus indented block scalars."""
    fields: dict = {}
    current = None
    for raw in fm_text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw[0] in " \t" and current is not None:
            fields[current] = (fields[current] + " " + raw.strip()).strip()
            continue
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", raw)
        if not m:
            current = None
            continue
        current, value = m.group(1), m.group(2).strip()
        if value in ("|", ">", "|-", ">-", "|+", ">+"):
            fields[current] = ""  # block scalar: fold following indented lines
        else:
            fields[current] = value.strip("\"'")
    return fields


def check_skill(path: Path) -> dict:
    findings: list = []

    def add(fid: str, sev: str, msg: str, fix: str = "") -> None:
        findings.append({"id": fid, "severity": sev, "message": msg, "fix": fix})

    text = path.read_text(encoding="utf-8")
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
            add("I01", "info",
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

    missing, runtime = [], []
    for ref in sorted(set(LOCAL_REF.findall(text))):
        if "<" in ref or ">" in ref:
            continue  # templated mention like suites/<skill-name>.json
        if (path.parent / ref).exists():
            continue
        line = next((ln for ln in text.splitlines() if ref in ln), "")
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
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        add("S00", "error", f"Invalid JSON: {exc}", "Fix the JSON syntax.")
        return {
            "tool": TOOL, "mode": "suite", "target": str(path), "ok": False,
            "hard_failures": 1, "warnings": 0, "infos": 0,
            "stats": {}, "checks": findings,
        }

    if isinstance(data, dict) and isinstance(data.get("cases"), list):
        cases = data["cases"]
        skill = data.get("skill")
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

    if n < 4:
        add("S04", "error", f"Only {n} cases — too thin to say anything.")
    elif n < 12:
        add("S04", "warn", f"{n} cases — default suite is 12 (8 positive / 4 negative).")
    if pos < 3:
        add("S05", "error", f"Only {pos} positive cases — recall is untested.")
    if neg < 2:
        add("S06", "error",
            f"Only {neg} negative cases — over-triggering goes undetected.")
    if pos and neg and pos < neg:
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
        "stats": {"skill": skill, "cases": n, "positive": pos, "negative": neg,
                  "borderline": sum(1 for c in cases if isinstance(c, dict)
                                    and c.get("should_trigger") == "borderline")},
        "checks": findings,
    }


def main(argv=None) -> int:
    class _Parser(argparse.ArgumentParser):
        def error(self, message):  # usage errors exit 1; 2 is reserved for hard failures
            print(json.dumps({"tool": TOOL, "ok": False,
                              "error": f"usage: {message}"}))
            sys.exit(1)

    ap = _Parser(description="trigger-doctor mechanical pre-flight")
    ap.add_argument("target",
                    help="SKILL.md path, skill directory, or suite .json (with --suite)")
    ap.add_argument("--suite", action="store_true",
                    help="validate a trigger suite JSON instead of a skill")
    args = ap.parse_args(argv)

    path = Path(args.target)
    if not path.exists():
        print(json.dumps({"tool": TOOL, "ok": False,
                          "error": f"target not found: {path}"}))
        return 1
    if path.is_dir():
        candidate = path / "SKILL.md"
        if not candidate.exists():
            print(json.dumps({"tool": TOOL, "ok": False,
                              "error": f"no SKILL.md in {path}"}))
            return 1
        path = candidate

    report = check_suite(path) if args.suite else check_skill(path)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
