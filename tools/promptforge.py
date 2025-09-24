# path: tools/promptforge.py
# purpose: PromptForge GUI/CLI; builds/validates model replies for ENTIRE FILES; enforces R5; copyable validation; tolerant start-sentinel; project-scoped Requirements CRUD with persistence and prompt injection
# timestamp: 2025-09-08T00:00:00Z
#!/usr/bin/env python3
# PromptForge — GUI + CLI for consistent, rule-driven AI prompts with per-project settings.
# Stdlib-only (tkinter + sqlite3 + zipfile), Windows-friendly. Stores config in .promptforge/config.json and SQLite in .promptforge/promptforge.db.
# v2.1 — Adds project-scoped Requirements (CRUD + enable/disable per project), injection into prompts, and per-prompt override + persist-selection.
#       — Keeps R5 commented headers/footers in-file; copyable validation report; tolerant start sentinel in validator.

import argparse
import json
import os
import sys
import textwrap
import datetime
import shutil
import sqlite3
import re
import hashlib
import zipfile
from typing import Any, Dict, List, Optional, Tuple

APP_DIR = os.path.join(".promptforge")
CONFIG_PATH = os.path.join(APP_DIR, "config.json")
OUTPUT_DIR = os.path.join(APP_DIR, "out")
DB_PATH = os.path.join(APP_DIR, "promptforge.db")


def now_stamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


DEFAULT_CONFIG: Dict[str, Any] = {
    "project_name": "",
    "rules": [
        {
            "id": "R1",
            "text": "Return ENTIRE FILES only in individual canvas, or packaged in a Zip package, never diffs or snippets.",
        },
        {
            "id": "R2",
            "text": "Preserve all logging / progress / history features unchanged.",
        },
        {"id": "R3", "text": "No prose outside file blocks. One file per block."},
        {
            "id": "R4",
            "text": "Deliver only smoke-tested, parsable, executable full files (no prose/headers). Validate syntax & imports; keep logging/progress/history; include dependencies.",
        },
        {
            "id": "R5",
            "text": "Preserve and update required file headers/footers. Include (at minimum) relative path, purpose/usage, and an ISO8601 timestamp at the top; include a footer with ending line-count if the project requires it. Do not remove/alter existing headers/footers—update them in place.",
        },
    ],
    "include_output_contract_in_prompts": True,
    "sentinels": {
        "start": "### FILE OUTPUT START  ###",
        "end": "END OF OUTPUT",
        "self_check_line": "✔ R1 ✔ R2 ✔ R3",
    },
    "output_contract": {
        "file_block": {
            "start": "```file",
            "end": "```",
            "fields": ["path", "language", "contents"],
            "example": textwrap.dedent("""
                ```file
                path: src/module.py
                language: python
                contents:
                <full file contents here>
                ```
            """).strip(),
            "help": {
                "start": "Opening fence that wraps a single file. The model must start a file block with this exact token.",
                "end": "Closing fence that terminates a file block.",
                "fields": "Required metadata keys the model must include at the top of each file block.",
                "example": "Reference block shown to the model to increase compliance.",
            },
        }
    },
    "r5": {
        "enforce": True,
        "header_search_lines": 15,
        "footer_search_lines": 10,
        "require_footer_line_count": True,
        "header_keys": {
            "path": r"path\s*:\s*.{1,}",
            "purpose_or_usage": r"(purpose|usage)\s*:\s*.{1,}",
            "timestamp": r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z\b",
        },
        "footer_line_count": r"(lines|line-count)\s*:\s*\d+",
    },
    "style": {"tone": "concise", "language": "en-US"},
    "scenarios": {
        "troubleshooting": {
            "title": "Troubleshooting",
            "description": "Provide debugging guidance and code changes while obeying rule R1 (full files) and R2 (logging preserved).",
            "sections": [
                {"label": "CONTEXT", "prompt": "Brief system/project context"},
                {"label": "ERRORS", "prompt": "Paste error messages/log excerpts"},
                {"label": "OBSERVED_BEHAVIOR", "prompt": "What happens now"},
                {"label": "EXPECTED_BEHAVIOR", "prompt": "What should happen"},
                {"label": "REPRO_STEPS", "prompt": "Steps to reproduce"},
            ],
            "extra_directives": [
                "When proposing code changes, emit ENTIRE FILES per OUTPUT CONTRACT.",
                "If multiple files are needed, emit one file block per file.",
                "If you must explain, create a separate META.md as a full file block.",
            ],
        },
        "refactor": {
            "title": "Refactor",
            "description": "Improve structure/clarity without changing public interfaces or removing logging/progress/history features.",
            "sections": [
                {"label": "CONTEXT", "prompt": "Current architecture notes"},
                {"label": "TARGETS", "prompt": "Files or modules to refactor"},
                {
                    "label": "GOALS",
                    "prompt": "What to improve (readability, cohesion, etc.)",
                },
                {"label": "CONSTRAINTS", "prompt": "Must-keep behaviors and APIs"},
            ],
            "extra_directives": [
                "Preserve all logging/progress/history features unchanged (R2).",
                "Emit ENTIRE FILES only (R1), no diffs.",
                "No prose outside file blocks (R3).",
            ],
        },
        "feature": {
            "title": "Feature",
            "description": "Add a new capability with full file outputs and preserved logging.",
            "sections": [
                {
                    "label": "USER_STORY",
                    "prompt": "As a <role> I want <feature> so that <benefit>",
                },
                {"label": "ACCEPTANCE_CRITERIA", "prompt": "List, numbered"},
                {"label": "AFFECTED_AREAS", "prompt": "Files/modules affected"},
                {"label": "NOTES", "prompt": "Edge cases, performance, i18n, etc."},
            ],
            "extra_directives": [
                "Emit entire files for any changed/added components (R1).",
                "Keep existing logging/progress/history intact (R2).",
                "No commentary outside file blocks; if needed, include META.md as a file.",
            ],
        },
        "review": {
            "title": "Code Review",
            "description": "Request targeted review with explicit outputs.",
            "sections": [
                {"label": "OBJECTIVE", "prompt": "What feedback you want"},
                {
                    "label": "FOCUS",
                    "prompt": "Performance, security, readability, etc.",
                },
                {"label": "FILES", "prompt": "Which files are in scope"},
            ],
            "extra_directives": [
                "If suggesting changes, provide ENTIRE FILES (R1).",
                "Never remove logging/progress/history (R2).",
            ],
        },
    },
    "help": {
        "fields": {
            "Project Name": "Optional label saved in config; appears in prompts.",
            "Scenario": "Preset that controls which sections appear and their purpose.",
            "Task": "1-line objective of this prompt. Be specific/measurable.",
            "Extra Notes": "Any additional constraints, links, or context.",
            "Sentinels": "Strings the assistant must echo to mark its output. Start and End help automations detect file blocks.",
            "Output Contract": "Defines how the model must wrap ENTIRE FILES in fenced blocks with required metadata.",
        }
    },
    "clipboard": True,
    "write_default_output_file": True,
}


# ------------------------------
# Utilities / persistence
# ------------------------------
def ensure_app_dirs() -> None:
    os.makedirs(APP_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_config() -> Dict[str, Any]:
    if not os.path.exists(CONFIG_PATH):
        return json.loads(json.dumps(DEFAULT_CONFIG))
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    have = {r.get("id") for r in cfg.get("rules", [])}
    if "R4" not in have:
        cfg.setdefault("rules", []).append(
            {"id": "R4", "text": DEFAULT_CONFIG["rules"][3]["text"]}
        )
    if "R5" not in have:
        cfg.setdefault("rules", []).append(
            {"id": "R5", "text": DEFAULT_CONFIG["rules"][4]["text"]}
        )
    cfg.setdefault("r5", DEFAULT_CONFIG["r5"])
    return cfg


def save_config(cfg: Dict[str, Any]) -> None:
    ensure_app_dirs()
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def win_clip_copy(text: str) -> bool:
    clip = shutil.which("clip")
    if not clip:
        return False
    try:
        p = os.popen("clip", "w")
        p.write(text)
        p.close()
        return True
    except Exception:
        return False


def print_hr():
    print("-" * 72)


# ------------------------------
# SQLite & History + Requirements
# ------------------------------
def ensure_db() -> None:
    ensure_app_dirs()
    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.cursor()
        # Prompts history
        cur.execute("""
            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                scenario TEXT NOT NULL,
                task TEXT NOT NULL,
                content TEXT NOT NULL
            )
        """)
        # Requirements catalog (global)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS requirements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                tag TEXT
            )
        """)
        # Project-to-requirement mapping (enabled flag persists selection)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS project_requirements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project TEXT NOT NULL,
                req_id INTEGER NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                UNIQUE(project, req_id),
                FOREIGN KEY(req_id) REFERENCES requirements(id) ON DELETE CASCADE
            )
        """)
        con.commit()
    finally:
        con.close()


def save_prompt_to_db(scenario: str, task: str, content: str) -> int:
    ensure_db()
    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO prompts (created_at, scenario, task, content) VALUES (?, ?, ?, ?)",
            (
                datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
                scenario,
                task,
                content,
            ),
        )
        con.commit()
        return cur.lastrowid
    finally:
        con.close()


def list_prompts(limit: int = 200) -> List[Tuple[int, str, str, str]]:
    ensure_db()
    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT id, created_at, scenario, task FROM prompts ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return list(cur.fetchall())
    finally:
        con.close()


def get_prompt_content(pid: int) -> Optional[str]:
    ensure_db()
    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.cursor()
        cur.execute("SELECT content FROM prompts WHERE id = ?", (pid,))
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        con.close()


# ----- Requirements helpers -----
def req_add(text: str, tag: Optional[str] = None) -> int:
    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO requirements(text, tag) VALUES(?, ?)",
            (text.strip(), tag.strip() if tag else None),
        )
        con.commit()
        return cur.lastrowid
    finally:
        con.close()


def req_update(req_id: int, text: str, tag: Optional[str]) -> None:
    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.cursor()
        cur.execute(
            "UPDATE requirements SET text=?, tag=? WHERE id=?",
            (text.strip(), tag.strip() if tag else None, req_id),
        )
        con.commit()
    finally:
        con.close()


def req_delete(req_id: int) -> None:
    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.cursor()
        cur.execute("DELETE FROM requirements WHERE id=?", (req_id,))
        cur.execute("DELETE FROM project_requirements WHERE req_id=?", (req_id,))
        con.commit()
    finally:
        con.close()


def req_list_all() -> List[Tuple[int, str, Optional[str]]]:
    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.cursor()
        cur.execute("SELECT id, text, tag FROM requirements ORDER BY id DESC")
        return list(cur.fetchall())
    finally:
        con.close()


def req_set_for_project(project: str, req_id: int, enabled: bool) -> None:
    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO project_requirements(project, req_id, enabled) VALUES(?, ?, ?)",
            (project.strip(), req_id, 1 if enabled else 0),
        )
        cur.execute(
            "UPDATE project_requirements SET enabled=? WHERE project=? AND req_id=?",
            (1 if enabled else 0, project.strip(), req_id),
        )
        con.commit()
    finally:
        con.close()


def req_list_for_project(project: str) -> List[Tuple[int, str, Optional[str], int]]:
    """
    Returns list of (req_id, text, tag, enabled) for the given project.
    If a requirement has no project mapping, it will not be returned unless you want to show all.
    """
    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.cursor()
        cur.execute(
            """
            SELECT r.id, r.text, r.tag, pr.enabled
            FROM project_requirements pr
            JOIN requirements r ON r.id = pr.req_id
            WHERE pr.project=?
            ORDER BY r.id DESC
        """,
            (project.strip(),),
        )
        return list(cur.fetchall())
    finally:
        con.close()


def req_list_all_with_project(
    project: str,
) -> List[Tuple[int, str, Optional[str], int]]:
    """
    Returns all requirements with enabled flag joined for this project (missing mapping treated as 0).
    """
    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.cursor()
        cur.execute(
            """
            SELECT r.id, r.text, r.tag,
                   COALESCE((SELECT enabled FROM project_requirements pr WHERE pr.req_id=r.id AND pr.project=?), 0) AS enabled
            FROM requirements r
            ORDER BY r.id DESC
        """,
            (project.strip(),),
        )
        return list(cur.fetchall())
    finally:
        con.close()


def req_enabled_texts(project: str) -> List[str]:
    return [
        t for (_id, t, _tag, en) in req_list_all_with_project(project) if int(en) == 1
    ]


# ------------------------------
# Prompt builders
# ------------------------------
def natural_rule_key(rule_id: str) -> Tuple[int, str]:
    m = re.match(r"^[Rr](\d+)$", rule_id.strip())
    if m:
        return (int(m.group(1)), rule_id)
    m2 = re.search(r"(\d+)$", rule_id)
    return (int(m2.group(1)) if m2 else 10**9, rule_id)


def sorted_rules(rules: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return sorted(rules, key=lambda r: natural_rule_key(r.get("id", "")))


def format_rules(cfg: Dict[str, Any], subset_ids: Optional[List[str]] = None) -> str:
    rules = cfg["rules"]
    if subset_ids is not None:
        only = {rid.strip() for rid in subset_ids}
        rules = [r for r in rules if r["id"] in only]
    rules = sorted_rules(rules)
    lines = ["RULES (read carefully; apply before anything else)"]
    for r in rules:
        lines.append(f"{r['id']}. {r['text']}")
    return "\n".join(lines)


def format_output_contract(cfg: Dict[str, Any]) -> str:
    if not cfg.get("include_output_contract_in_prompts", True):
        return ""
    fc = cfg["output_contract"]["file_block"]
    example = fc.get("example", "").strip()
    lines = [
        "OUTPUT CONTRACT",
        f"- Use file blocks delimited by: {fc['start']} ... {fc['end']}",
        f"- Fields required in each block: {', '.join(fc['fields'])}",
        "- One file per block. Emit ENTIRE FILES only.",
        "",
        "EXAMPLE",
        example,
    ]
    return "\n".join(lines)


def format_sentinels(cfg: Dict[str, Any]) -> str:
    s = cfg["sentinels"]
    return textwrap.dedent(f"""
        SENTINELS
        - Start marker: {s['start']}
        - End marker: {s['end']}
        - Self-check line (must appear before first file block): {s['self_check_line']}
    """).strip()


def format_requirements_block(project: str, selected_reqs: List[str]) -> str:
    if not selected_reqs:
        return ""
    lines = ["REQUIREMENTS (project-specific)"]
    for t in selected_reqs:
        lines.append(f"- {t}")
    lines.append("")  # blank line after section
    return "\n".join(lines)


def build_prompt(
    cfg: Dict[str, Any],
    scenario_key: str,
    task: str,
    section_inputs: Dict[str, str],
    extra_text: Optional[str] = None,
    rule_ids_subset: Optional[List[str]] = None,
    project: Optional[str] = None,
    selected_requirements: Optional[List[str]] = None,
) -> str:
    scenario = cfg["scenarios"][scenario_key]
    s = cfg["sentinels"]
    header: List[str] = [
        format_rules(cfg, subset_ids=rule_ids_subset),
    ]

    # Insert project-specific requirements directly beneath RULES
    if project:
        reqs_to_include = (
            selected_requirements
            if selected_requirements is not None
            else req_enabled_texts(project)
        )
        if reqs_to_include:
            header += [
                "",
                format_requirements_block(project, reqs_to_include).rstrip("\n"),
            ]

    oc_text = format_output_contract(cfg)
    if oc_text:
        header += ["", oc_text]
    header += [
        "",
        format_sentinels(cfg),
        "",
        f"SCENARIO: {scenario['title']}",
        f"DESCRIPTION: {scenario['description']}",
        "",
    ]
    header.append("TASK")
    header.append(task.strip())
    header.append("")
    for sec in scenario["sections"]:
        label = sec["label"]
        val = section_inputs.get(label, "").strip()
        header.append(label)
        header.append(val if val else "(none)")
        header.append("")
    if scenario.get("extra_directives"):
        header.append("EXTRA DIRECTIVES")
        for d in scenario["extra_directives"]:
            header.append(f"- {d}")
        header.append("")
    if extra_text:
        header.append("NOTES")
        header.append(extra_text.strip())
        header.append("")
    header.append("RESPONSE REQUIREMENTS")
    header.append("1) First line must be the self-check line exactly as below.")
    header.append("2) Then emit the start sentinel.")
    header.append("3) Then only file blocks per OUTPUT CONTRACT.")
    header.append("4) Finish with the end sentinel.")
    header.append("")
    header.append("SELF-CHECK LINE")
    header.append(s["self_check_line"])
    header.append("")
    header.append("BEGIN RESPONSE WITH:")
    header.append(s["self_check_line"])
    header.append(s["start"])
    return "\n".join(header).strip() + "\n"


def parse_prompt_to_fields(
    cfg: Dict[str, Any], scenario_key: str, content: str
) -> Tuple[str, Dict[str, str]]:
    task = ""
    sections: Dict[str, str] = {}
    lines = content.splitlines()
    for i, ln in enumerate(lines):
        if ln.strip() == "TASK" and i + 1 < len(lines):
            task = lines[i + 1].strip()
            break
    scenario = cfg["scenarios"].get(scenario_key, {})
    labels = [s["label"] for s in scenario.get("sections", [])]
    idxs: Dict[str, int] = {}
    for i, ln in enumerate(lines):
        if ln.strip() in labels:
            idxs[ln.strip()] = i
    footer_markers = {
        "EXTRA DIRECTIVES",
        "NOTES",
        "RESPONSE REQUIREMENTS",
        "SELF-CHECK LINE",
        "BEGIN RESPONSE WITH:",
    }
    for lbl in labels:
        if lbl not in idxs:
            continue
        start = idxs[lbl] + 1
        next_pos = len(lines)
        for k in range(start, len(lines)):
            if lines[k].strip() in labels or lines[k].strip() in footer_markers:
                next_pos = k
                break
        val = "\n".join(lines[start:next_pos]).strip()
        sections[lbl] = val
    return task, sections


# ---------------- CLI ----------------
def run_wizard(cfg: Dict[str, Any]) -> Dict[str, Any]:
    print("PromptForge Wizard — set per-project defaults. Press Enter to keep current.")
    print_hr()
    proj = input(f"Project name [{cfg.get('project_name','')}]: ").strip()
    if proj:
        cfg["project_name"] = proj
    print_hr()
    print("Current RULES:")
    for r in sorted_rules(cfg["rules"]):
        print(f"- {r['id']}: {r['text']}")
    print("Edit rules? (y/N): ", end="")
    if input().strip().lower() == "y":
        new_rules: List[Dict[str, str]] = []
        print("Enter rules one per line as: ID | Text. Blank line to finish.")
        while True:
            line = input("Rule: ").strip()
            if not line:
                break
            if "|" in line:
                rid, rtext = [x.strip() for x in line.split("|", 1)]
                new_rules.append({"id": rid, "text": rtext})
            else:
                print("Use 'ID | Text' format.")
        if new_rules:
            cfg["rules"] = sorted_rules(new_rules)
    print_hr()
    s = cfg["sentinels"]
    s["start"] = input(f"Start sentinel [{s['start']}]: ").strip() or s["start"]
    s["end"] = input(f"End sentinel [{s['end']}]: ").strip() or s["end"]
    s["self_check_line"] = (
        input(f"Self-check line [{s['self_check_line']}]: ").strip()
        or s["self_check_line"]
    )
    print_hr()
    print(
        f"Include Output Contract in prompts? (Y/n) [current: {cfg.get('include_output_contract_in_prompts', True)}]: ",
        end="",
    )
    incl = input().strip().lower()
    if incl in ("y", "n"):
        cfg["include_output_contract_in_prompts"] = incl != "n"
    print_hr()
    print("Edit output contract file block settings? (y/N): ", end="")
    if input().strip().lower() == "y":
        fb = cfg["output_contract"]["file_block"]
        fb["start"] = (
            input(f"Block start fence [{fb['start']}]: ").strip() or fb["start"]
        )
        fb["end"] = input(f"Block end fence [{fb['end']}]: ").strip() or fb["end"]
        fields_line = input(
            f"Fields CSV {fb['fields']} (press Enter to keep): "
        ).strip()
        if fields_line:
            fb["fields"] = [x.strip() for x in fields_line.split(",") if x.strip()]
    print_hr()
    r5 = cfg.setdefault("r5", DEFAULT_CONFIG["r5"])
    print(f"Enforce R5? (Y/n) [current: {r5.get('enforce', True)}]: ", end="")
    ans = input().strip().lower()
    if ans in ("y", "n"):
        r5["enforce"] = ans != "n"
    save_config(cfg)
    print("\nSaved:", CONFIG_PATH)
    return cfg


def cmd_init(_args: argparse.Namespace) -> None:
    ensure_app_dirs()
    if os.path.exists(CONFIG_PATH):
        print("Config already exists:", CONFIG_PATH)
        return
    save_config(json.loads(json.dumps(DEFAULT_CONFIG)))
    ensure_db()
    print("Initialized default config at", CONFIG_PATH)


def cmd_show(_args: argparse.Namespace) -> None:
    cfg = load_config()
    print(json.dumps(cfg, indent=2, ensure_ascii=False))


def cmd_wizard(_args: argparse.Namespace) -> None:
    cfg = load_config()
    run_wizard(cfg)


def collect_sections(
    cfg: Dict[str, Any], scenario_key: str, args: argparse.Namespace
) -> Dict[str, str]:
    scenario = cfg["scenarios"][scenario_key]
    result: Dict[str, str] = {}
    file_map: Dict[str, str] = {}
    if getattr(args, "errors", None):
        file_map["ERRORS"] = read_text_file(args.errors)
    if getattr(args, "context", None):
        file_map["CONTEXT"] = read_text_file(args.context)
    if getattr(args, "notes", None):
        file_map["NOTES"] = read_text_file(args.notes)
    for sec in scenario["sections"]:
        label = sec["label"]
        if label in file_map:
            result[label] = file_map[label]
            continue
        if getattr(args, "sections_json", None):
            try:
                sj = json.loads(args.sections_json)
                if label in sj and isinstance(sj[label], str):
                    result[label] = sj[label]
                    continue
            except Exception:
                pass
        result[label] = ""
    return result


def cmd_make(args: argparse.Namespace) -> None:
    cfg = load_config()
    scenario_key = args.scenario
    if scenario_key not in cfg["scenarios"]:
        print(
            f"Unknown scenario '{scenario_key}'. Available: {', '.join(cfg['scenarios'].keys())}"
        )
        sys.exit(1)
    section_inputs = collect_sections(cfg, scenario_key, args)
    extra_text = args.extra if getattr(args, "extra", None) else None
    project = cfg.get("project_name", "")
    # Use persisted enabled requirements as default
    req_texts = req_enabled_texts(project) if project else []
    prompt = build_prompt(
        cfg,
        scenario_key,
        args.task.strip(),
        section_inputs,
        extra_text,
        rule_ids_subset=None,
        project=project,
        selected_requirements=req_texts,
    )
    print_hr()
    print(prompt)
    print_hr()
    ensure_app_dirs()
    out_file = os.path.join(OUTPUT_DIR, f"prompt_{scenario_key}_{now_stamp()}.txt")
    if cfg.get("write_default_output_file", True):
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(prompt)
        print("Saved:", out_file)
    if cfg.get("clipboard", True):
        win_clip_copy(prompt)
    if getattr(args, "save_to_db", False):
        pid = save_prompt_to_db(scenario_key, args.task.strip(), prompt)
        print(f"Saved to DB with id {pid}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="PromptForge: build consistent, rule-driven AI prompts with per-project config."
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser(
        "init", help="Create default .promptforge/config.json in current project."
    )
    sp.set_defaults(func=cmd_init)

    sp = sub.add_parser("show", help="Show current config JSON.")
    sp.set_defaults(func=cmd_show)

    sp = sub.add_parser(
        "wizard",
        help="Interactive setup/update of rules, sentinels, output contract, options.",
    )
    sp.set_defaults(func=cmd_wizard)

    sp = sub.add_parser("make", help="Generate a prompt using a scenario and task.")
    sp.add_argument(
        "--scenario", required=True, choices=list(DEFAULT_CONFIG["scenarios"].keys())
    )
    sp.add_argument("--task", required=True)
    sp.add_argument("--errors")
    sp.add_argument("--context")
    sp.add_argument("--notes")
    sp.add_argument("--sections_json")
    sp.add_argument("--extra")
    sp.add_argument(
        "--save_to_db",
        action="store_true",
        help="Also store the generated prompt in the local DB.",
    )
    sp.set_defaults(func=cmd_make)

    sp = sub.add_parser("gui", help="Launch PromptForge GUI.")
    sp.set_defaults(func=lambda _args: run_gui())

    return p.parse_args()


# ------------------------------
# Simple ToolTip helper (Tkinter)
# ------------------------------
class ToolTip:
    """Lightweight tooltip that performs a lazy import of tkinter to avoid NameError.
    Attaches to any Tk widget and shows text after a delay. Works with Python 3.13.
    """

    def __init__(self, widget, text: str = "", delay_ms: int = 500):
        self.widget = widget
        self.text = text
        self.delay = delay_ms
        self._id = None
        self._tip = None
        self.widget.bind("<Enter>", self._schedule)
        self.widget.bind("<Leave>", self._hide)

    def _schedule(self, _event=None):
        self._cancel()
        self._id = self.widget.after(self.delay, self._show)

    def _cancel(self):
        if self._id:
            try:
                self.widget.after_cancel(self._id)
            except Exception:
                pass
            self._id = None

    def _show(self):
        if self._tip or not self.text:
            return
        import tkinter as tkmod

        try:
            x, y, cx, cy = self.widget.bbox("insert")
        except Exception:
            x, y = 0, 0
        x += self.widget.winfo_rootx() + 20
        y += self.widget.winfo_rooty() + 20
        self._tip = tw = tkmod.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tkmod.Label(
            tw,
            text=self.text,
            justify="left",
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            wraplength=360,
        )
        label.pack(ipadx=4, ipady=2)

    def _hide(self, _event=None):
        self._cancel()
        if self._tip:
            try:
                self._tip.destroy()
            except Exception:
                pass
            self._tip = None


# -------------- R5 helpers (comment-aware) --------------
_LANG_COMMENTS = {
    "python": ["#"],
    "py": ["#"],
    "javascript": ["//", "/*", "*", "*/"],
    "typescript": ["//", "/*", "*", "*/"],
    "java": ["//", "/*", "*", "*/"],
    "c": ["//", "/*", "*", "*/"],
    "cpp": ["//", "/*", "*", "*/"],
    "csharp": ["//", "/*", "*", "*/"],
    "go": ["//", "/*", "*", "*/"],
    "rust": ["//", "/*", "*", "*/"],
    "kotlin": ["//", "/*", "*", "*/"],
    "swift": ["//", "/*", "*", "*/"],
    "php": ["//", "/*", "*", "*/", "#"],
    "ruby": ["#"],
    "shell": ["#"],
    "bash": ["#"],
    "powershell": ["#"],
    "haskell": ["--"],
    "lua": ["--"],
    "r": ["#"],
    "markdown": ["<!--", ">"],
    "md": ["<!--", ">"],
    "html": ["<!--"],
    "xml": ["<!--"],
    "css": ["/*", "*", "*/"],
    "sql": ["--", "#"],
}


def _strip_comment_prefix(line: str, language: str) -> Optional[str]:
    tokens = _LANG_COMMENTS.get(language.lower(), ["#"])
    s = line.lstrip()
    for t in tokens:
        if s.startswith(t):
            return s[len(t) :].strip()
    if language.lower() in ("markdown", "md"):
        return s
    return None


def _iso8601_regex() -> re.Pattern:
    return re.compile(
        r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z\b", re.IGNORECASE
    )


def _match_any_rx(pattern: str, lines: List[str]) -> bool:
    rx = re.compile(pattern, re.IGNORECASE)
    return any(rx.search(ln) for ln in lines)


def _r5_check(cfg: Dict[str, Any], file_record: Dict[str, Any]) -> Dict[str, Any]:
    r5 = cfg.get("r5", {})
    issues: List[str] = []
    contents = file_record.get("contents", "")
    lang = (file_record.get("language") or "").lower()
    lines = contents.splitlines()

    header_n = int(r5.get("header_search_lines", 15) or 15)
    footer_n = int(r5.get("footer_search_lines", 10) or 10)
    header_chunk = lines[:header_n]
    footer_chunk = lines[-footer_n:] if footer_n > 0 else []

    header_comments: List[str] = []
    for ln in header_chunk:
        stripped = _strip_comment_prefix(ln, lang)
        if stripped is not None:
            header_comments.append(stripped)

    footer_comments: List[str] = []
    for ln in footer_chunk:
        stripped = _strip_comment_prefix(ln, lang)
        if stripped is not None:
            footer_comments.append(stripped)

    hk = r5.get("header_keys", {})
    if not _match_any_rx(hk.get("path", r"path\s*:\s*.+"), header_comments):
        issues.append("R5 header: missing commented 'path:' line")
    if not _match_any_rx(
        hk.get("purpose_or_usage", r"(purpose|usage)\s*:\s*.+"), header_comments
    ):
        issues.append("R5 header: missing commented 'purpose:' or 'usage:' line")
    ts_pat = hk.get("timestamp", _iso8601_regex().pattern)
    if not _match_any_rx(ts_pat, header_comments):
        issues.append(
            "R5 header: missing ISO8601 'timestamp' in comments (e.g., 2025-01-30T12:34:56Z)"
        )
    if r5.get("require_footer_line_count", True):
        if not _match_any_rx(
            r5.get("footer_line_count", r"(lines|line-count)\s*:\s*\d+"),
            footer_comments,
        ):
            issues.append("R5 footer: missing commented 'lines:' or 'line-count:'")
    return {"ok": not issues, "issues": issues}


class ParsedFileBlock(Tuple[str, str, str]):
    __slots__ = ()


# -------------- Reply parser / validator --------------
def parse_ai_reply(cfg: Dict[str, Any], raw: str) -> Dict[str, Any]:
    s = cfg["sentinels"]
    fb = cfg["output_contract"]["file_block"]
    fields = fb["fields"]
    start_fence = fb["start"].strip()
    end_fence = fb["end"].strip()

    result = {
        "has_self_check": False,
        "has_start": False,
        "has_end": False,
        "files": [],
        "errors": [],
    }
    if s["self_check_line"] in raw:
        result["has_self_check"] = True

    start_ok = False
    if s["start"] and s["start"] in raw:
        start_ok = True
    else:
        if re.search(r"(?m)^\s*###\s*FILE OUTPUT START(?:\s+.*)?###\s*$", raw):
            start_ok = True
    result["has_start"] = start_ok

    if s["end"] and s["end"] in raw:
        result["has_end"] = True
    else:
        if re.search(r"(?m)^\s*END OF OUTPUT\s*$", raw):
            result["has_end"] = True

    block_re = re.compile(
        rf"{re.escape(start_fence)}\s*\n(.*?){re.escape(end_fence)}", re.S
    )
    matches = list(block_re.finditer(raw))
    if not matches:
        result["errors"].append("No file blocks found using configured fences.")
        return result

    for m in matches:
        block = m.group(1)
        header_lines: List[str] = []
        content_start_idx = None
        lines = block.splitlines()
        for idx, ln in enumerate(lines):
            if ln.strip().lower().startswith("contents:"):
                content_start_idx = idx + 1
                break
            header_lines.append(ln)

        if content_start_idx is None:
            result["errors"].append("A file block missing 'contents:' line; skipped.")
            continue

        header_map: Dict[str, str] = {}
        for hl in header_lines:
            if ":" in hl:
                key, val = hl.split(":", 1)
                header_map[key.strip().lower()] = val.strip()

        missing = [f for f in fields if f.lower() not in header_map]
        if missing:
            result["errors"].append(
                f"Missing required header fields: {', '.join(missing)}"
            )
            continue

        path_val = header_map.get("path", "")
        lang_val = header_map.get("language", "")
        contents = "\n".join(lines[content_start_idx:])

        line_count = len(contents.splitlines())
        sha = hashlib.sha256(contents.encode("utf-8")).hexdigest()

        rec = {
            "path": path_val,
            "language": lang_val,
            "contents": contents,
            "lines": line_count,
            "sha256": sha,
        }
        if cfg.get("r5", {}).get("enforce", True):
            rec["r5"] = _r5_check(cfg, rec)

        result["files"].append(rec)

    if not result["files"]:
        result["errors"].append("No valid files parsed.")
    return result


def save_parsed_files_to_folder(parsed: Dict[str, Any], base_dir: str) -> List[str]:
    written: List[str] = []
    for f in parsed.get("files", []):
        rel = f["path"].replace("\\", "/").lstrip("/")
        abspath = os.path.join(base_dir, rel)
        os.makedirs(os.path.dirname(abspath), exist_ok=True)
        with open(abspath, "w", encoding="utf-8") as out:
            out.write(f["contents"])
        written.append(abspath)
    return written


def export_parsed_to_zip(parsed: Dict[str, Any], zip_path: str) -> str:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f in parsed.get("files", []):
            rel = f["path"].replace("\\", "/").lstrip("/")
            zf.writestr(rel, f["contents"])
    return zip_path


# -------------- GUI --------------
def run_gui() -> None:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog

    cfg = load_config()
    ensure_db()

    root = tk.Tk()
    root.title("PromptForge GUI")
    root.geometry("1400x1020")

    # Menu
    menubar = tk.Menu(root)
    filemenu = tk.Menu(menubar, tearoff=0)

    def harvest_all():
        cfg["project_name"] = proj_var.get().strip()
        cfg["sentinels"]["start"] = s_start.get().strip()
        cfg["sentinels"]["end"] = s_end.get().strip()
        cfg["sentinels"]["self_check_line"] = s_check.get().strip()
        cfg["include_output_contract_in_prompts"] = bool(include_oc_var.get())
        fb = cfg["output_contract"]["file_block"]
        fb["start"] = fb_start.get().strip()
        fb["end"] = fb_end.get().strip()
        fb["fields"] = [x.strip() for x in fb_fields.get().split(",") if x.strip()]
        fb["example"] = fb_example.get("1.0", "end").strip()
        r5cfg = cfg.setdefault("r5", DEFAULT_CONFIG["r5"])
        r5cfg["enforce"] = bool(r5_enforce_var.get())

        new_rules: List[Dict[str, str]] = []
        for item in rules_tree.get_children():
            rid, txt = rules_tree.item(item, "values")
            new_rules.append({"id": rid, "text": txt})
        cfg["rules"] = sorted_rules(new_rules)

    def rebuild_all():
        proj_var.set(cfg.get("project_name", ""))
        s_start.set(cfg["sentinels"]["start"])
        s_end.set(cfg["sentinels"]["end"])
        s_check.set(cfg["sentinels"]["self_check_line"])
        include_oc_var.set(
            1 if cfg.get("include_output_contract_in_prompts", True) else 0
        )
        fb2 = cfg["output_contract"]["file_block"]
        fb_start.set(fb2["start"])
        fb_end.set(fb2["end"])
        fb_fields.set(", ".join(fb2["fields"]))
        fb_example.delete("1.0", "end")
        fb_example.insert("1.0", fb2.get("example", ""))
        r5cfg = cfg.setdefault("r5", DEFAULT_CONFIG["r5"])
        r5_enforce_var.set(1 if r5cfg.get("enforce", True) else 0)

        refresh_rules()
        refresh_scenarios()
        rebuild_sections()
        refresh_help_lists()
        refresh_history()
        refresh_rules_selector()
        refresh_req_selector()
        refresh_req_tab()

    def do_load():
        path = filedialog.askopenfilename(
            title="Open config JSON", filetypes=[("JSON", "*.json")]
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    newcfg = json.load(f)
                cfg.clear()
                cfg.update(newcfg)
                save_config(cfg)
                messagebox.showinfo("Loaded", f"Config loaded from {path}")
                rebuild_all()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load: {e}")

    def do_save():
        try:
            harvest_all()
            save_config(cfg)
            messagebox.showinfo("Saved", f"Config saved to {CONFIG_PATH}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")

    def do_export_as():
        harvest_all()
        path = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON", "*.json")]
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Exported", f"Config exported to {path}")

    def do_import():
        path = filedialog.askopenfilename(
            title="Import JSON into current config", filetypes=[("JSON", "*.json")]
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    newcfg = json.load(f)
                cfg.clear()
                cfg.update(newcfg)
                messagebox.showinfo("Imported", "Config imported. Remember to Save.")
                rebuild_all()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import: {e}")

    menubar.add_cascade(label="File", menu=filemenu)
    filemenu.add_command(label="Load Config...", command=do_load)
    filemenu.add_command(label="Save Config", command=do_save)
    filemenu.add_command(label="Export As...", command=do_export_as)
    filemenu.add_command(label="Import Into Current...", command=do_import)
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=root.destroy)
    root.config(menu=menubar)

    nb = ttk.Notebook(root)
    nb.pack(fill="both", expand=True)

    # ----- Prompt Tab -----
    tab_prompt = ttk.Frame(nb)
    nb.add(tab_prompt, text="Prompt")
    tab_prompt.grid_columnconfigure(3, weight=1)
    for i in (2, 4, 7):
        tab_prompt.grid_rowconfigure(i, weight=1)

    proj_var = tk.StringVar(value=cfg.get("project_name", ""))
    ttk.Label(tab_prompt, text="Project Name").grid(row=0, column=0, sticky="w")
    proj_entry = ttk.Entry(tab_prompt, textvariable=proj_var, width=40)
    proj_entry.grid(row=0, column=1, sticky="ew")
    ToolTip(
        proj_entry, text=cfg.get("help", {}).get("fields", {}).get("Project Name", "")
    )

    def on_project_changed(*_a):
        refresh_req_selector()

    proj_var.trace_add("write", on_project_changed)

    scenario_keys = list(cfg["scenarios"].keys()) or ["troubleshooting"]
    scenario_var = tk.StringVar(value=scenario_keys[0])
    ttk.Label(tab_prompt, text="Scenario").grid(row=0, column=2, sticky="w")
    scenario_menu = ttk.Combobox(
        tab_prompt,
        textvariable=scenario_var,
        values=scenario_keys,
        state="readonly",
        width=24,
    )
    scenario_menu.grid(row=0, column=3, sticky="ew")
    ToolTip(
        scenario_menu, text=cfg.get("help", {}).get("fields", {}).get("Scenario", "")
    )

    task_var = tk.StringVar()
    ttk.Label(tab_prompt, text="Task").grid(row=1, column=0, sticky="w")
    task_entry = ttk.Entry(tab_prompt, textvariable=task_var)
    task_entry.grid(row=1, column=1, columnspan=3, sticky="ew")
    ToolTip(task_entry, text=cfg.get("help", {}).get("fields", {}).get("Task", ""))

    # Rules subset selector
    rules_selector_frame = ttk.LabelFrame(tab_prompt, text="Rules to include")
    rules_selector_frame.grid(
        row=2, column=0, columnspan=4, sticky="nsew", pady=6, padx=2
    )
    rules_listbox = tk.Listbox(
        rules_selector_frame, selectmode="extended", exportselection=False, height=5
    )
    rules_listbox.pack(fill="both", expand=True, padx=4, pady=4)
    ToolTip(
        rules_listbox,
        text="Select which rules to include in the prompt. Default: all selected.",
    )

    def refresh_rules_selector():
        rules_listbox.delete(0, "end")
        for r in sorted_rules(cfg["rules"]):
            rules_listbox.insert("end", f"{r['id']}: {r['text']}")
        rules_listbox.select_set(0, "end")

    sections_frame = ttk.Frame(tab_prompt)
    sections_frame.grid(row=3, column=0, columnspan=4, sticky="nsew", pady=6)
    section_widgets: Dict[str, Any] = {}

    def rebuild_sections(*_args):
        for w in sections_frame.winfo_children():
            w.destroy()
        section_widgets.clear()
        sc_key = scenario_var.get()
        sc = cfg["scenarios"][sc_key]
        sc_help = cfg.get("help", {}).get("scenarios", {}).get(sc_key, {})
        sec_help_map = sc_help.get("sections", {})
        for idx, sec in enumerate(sc["sections"]):
            label = sec["label"]
            ttk.Label(sections_frame, text=label).grid(row=idx, column=0, sticky="nw")
            txt = tk.Text(sections_frame, height=3, wrap="word")
            txt.grid(row=idx, column=1, sticky="nsew", padx=4, pady=2)
            ToolTip(txt, text=sec_help_map.get(label, ""))
            section_widgets[label] = txt
            sections_frame.grid_rowconfigure(idx, weight=1)
        sections_frame.grid_columnconfigure(1, weight=1)

    scenario_menu.bind("<<ComboboxSelected>>", rebuild_sections)
    rebuild_sections()

    extra_var = tk.StringVar()
    ttk.Label(tab_prompt, text="Extra Notes").grid(row=4, column=0, sticky="w")
    extra_entry = ttk.Entry(tab_prompt, textvariable=extra_var)
    extra_entry.grid(row=4, column=1, columnspan=3, sticky="ew")
    ToolTip(
        extra_entry, text=cfg.get("help", {}).get("fields", {}).get("Extra Notes", "")
    )

    # Project Requirements selector (two-tier: project -> requirements)
    req_selector_frame = ttk.LabelFrame(
        tab_prompt,
        text="Project Requirements (included at top of prompt; default = enabled for this project)",
    )
    req_selector_frame.grid(
        row=5, column=0, columnspan=4, sticky="nsew", pady=6, padx=2
    )
    req_selector_frame.grid_columnconfigure(1, weight=1)
    req_list = tk.Listbox(
        req_selector_frame, selectmode="extended", exportselection=False, height=6
    )
    req_list.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=4, pady=4)
    ToolTip(
        req_list,
        text="Checked/selected items will be added under REQUIREMENTS. Defaults come from the Requirements tab (enabled for this project).",
    )

    def refresh_req_selector():
        project = proj_var.get().strip()
        req_list.delete(0, "end")
        if not project:
            return
        items = req_list_all_with_project(project)
        for _id, text, tag, enabled in items:
            prefix = "[✓] " if int(enabled) == 1 else "[ ] "
            display = f"{prefix}{text}" if not tag else f"{prefix}{text}  ({tag})"
            req_list.insert("end", display)
            if int(enabled) == 1:
                req_list.select_set("end")

    def persist_selected_as_default():
        project = proj_var.get().strip()
        if not project:
            messagebox.showerror("No Project", "Enter a Project Name first.")
            return
        items = req_list_all_with_project(project)
        selected_idxs = set(req_list.curselection())
        for idx, (req_id, _text, _tag, _enabled) in enumerate(items):
            req_set_for_project(project, req_id, enabled=(idx in selected_idxs))
        messagebox.showinfo("Saved", f"Selection persisted for project '{project}'.")
        refresh_req_selector()

    ttk.Button(
        req_selector_frame,
        text="Save Selection as Default",
        command=persist_selected_as_default,
    ).grid(row=1, column=0, sticky="w", padx=4, pady=2)

    output = tk.Text(tab_prompt, height=16, wrap="word")
    output.grid(row=7, column=0, columnspan=4, sticky="nsew")

    def get_selected_rule_ids() -> Optional[List[str]]:
        sel = list(rules_listbox.curselection())
        if not sel:
            return None
        ids: List[str] = []
        for idx in sel:
            item = rules_listbox.get(idx)
            rid = item.split(":")[0].strip()
            ids.append(rid)
        return ids

    def current_selected_requirements_texts() -> List[str]:
        project = proj_var.get().strip()
        if not project:
            return []
        items = req_list_all_with_project(project)
        chosen_texts: List[str] = []
        selected_idxs = set(req_list.curselection())
        for idx, (_id, text, _tag, _enabled) in enumerate(items):
            if idx in selected_idxs:
                chosen_texts.append(text)
        # If nothing selected, fall back to enabled defaults
        return chosen_texts or req_enabled_texts(project)

    def build_prompt_click():
        harvest_all()
        section_inputs = {
            label: w.get("1.0", "end").strip() for label, w in section_widgets.items()
        }
        chosen_rules = get_selected_rule_ids()
        requirements_texts = current_selected_requirements_texts()
        prompt = build_prompt(
            cfg,
            scenario_var.get(),
            task_var.get().strip(),
            section_inputs,
            extra_var.get().strip(),
            chosen_rules,
            project=proj_var.get().strip(),
            selected_requirements=requirements_texts,
        )
        output.delete("1.0", "end")
        output.insert("1.0", prompt)
        if cfg.get("clipboard", True):
            try:
                root.clipboard_clear()
                root.clipboard_append(prompt)
            except Exception:
                pass

    def save_prompt_file_click():
        prompt_text = output.get("1.0", "end").strip()
        if not prompt_text:
            messagebox.showerror("No Prompt", "Build a prompt first.")
            return
        ensure_app_dirs()
        out_path = os.path.join(
            OUTPUT_DIR, f"prompt_{scenario_var.get()}_{now_stamp()}.txt"
        )
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(prompt_text)
        messagebox.showinfo("Saved", f"Prompt saved to {out_path}")

    def save_prompt_db_click():
        prompt_text = output.get("1.0", "end").strip()
        if not prompt_text:
            messagebox.showerror("No Prompt", "Build a prompt first.")
            return
        pid = save_prompt_to_db(scenario_var.get(), task_var.get().strip(), prompt_text)
        messagebox.showinfo("Saved", f"Prompt saved to DB with id {pid}")
        refresh_history()

    ttk.Button(tab_prompt, text="Build Prompt", command=build_prompt_click).grid(
        row=8, column=0, sticky="ew"
    )
    ttk.Button(tab_prompt, text="Save to File", command=save_prompt_file_click).grid(
        row=8, column=1, sticky="ew"
    )
    ttk.Button(tab_prompt, text="Save to DB", command=save_prompt_db_click).grid(
        row=8, column=2, sticky="ew"
    )

    # ----- Rules Tab -----
    tab_rules = ttk.Frame(nb)
    nb.add(tab_rules, text="Rules")
    tab_rules.grid_columnconfigure(2, weight=1)
    tab_rules.grid_rowconfigure(0, weight=1)

    rules_tree = ttk.Treeview(
        tab_rules, columns=("id", "text"), show="headings", height=10
    )
    rules_tree.heading("id", text="ID")
    rules_tree.heading("text", text="Text")
    rules_tree.grid(row=0, column=0, columnspan=3, sticky="nsew")

    rule_id_var = tk.StringVar()
    rule_text_var = tk.StringVar()

    ttk.Label(tab_rules, text="ID").grid(row=1, column=0, sticky="w")
    rule_id_entry = ttk.Entry(tab_rules, textvariable=rule_id_var, width=10)
    rule_id_entry.grid(row=1, column=1, sticky="w")
    ToolTip(
        rule_id_entry,
        text="Short identifier like R1, R2... Natural sort enforces R1<R2<R10.",
    )

    ttk.Label(tab_rules, text="Text").grid(row=2, column=0, sticky="w")
    rule_text_entry = ttk.Entry(tab_rules, textvariable=rule_text_var)
    rule_text_entry.grid(row=2, column=1, columnspan=2, sticky="ew")
    ToolTip(rule_text_entry, text="Edit the selected rule text or enter a new one.")

    def refresh_rules():
        rules_tree.delete(*rules_tree.get_children())
        for r in sorted_rules(cfg["rules"]):
            rules_tree.insert("", "end", values=(r["id"], r["text"]))

    def on_rule_select(_evt=None):
        sel = rules_tree.selection()
        if not sel:
            return
        rid, txt = rules_tree.item(sel[0], "values")
        rule_id_var.set(rid)
        rule_text_var.set(txt)

    def add_rule():
        rid = rule_id_var.get().strip()
        txt = rule_text_var.get().strip()
        if not rid or not txt:
            messagebox.showerror("Missing", "Both ID and Text are required.")
            return
        for r in cfg["rules"]:
            if r["id"] == rid:
                messagebox.showerror(
                    "Duplicate", f"Rule {rid} already exists. Use Update instead."
                )
                return
        cfg["rules"].append({"id": rid, "text": txt})
        cfg["rules"] = sorted_rules(cfg["rules"])
        refresh_rules()
        refresh_rules_selector()

    def update_rule():
        rid = rule_id_var.get().strip()
        txt = rule_text_var.get().strip()
        if not rid:
            messagebox.showerror("Missing", "Select a rule to update.")
            return
        found = False
        for r in cfg["rules"]:
            if r["id"] == rid:
                r["text"] = txt
                found = True
                break
        if not found:
            messagebox.showerror("Not Found", f"Rule {rid} not found. Use Add.")
            return
        cfg["rules"] = sorted_rules(cfg["rules"])
        refresh_rules()
        refresh_rules_selector()

    def del_rule():
        sel = rules_tree.selection()
        if not sel:
            return
        rid, _ = rules_tree.item(sel[0], "values")
        cfg["rules"] = [r for r in cfg["rules"] if r["id"] != rid]
        cfg["rules"] = sorted_rules(cfg["rules"])
        refresh_rules()
        refresh_rules_selector()
        rule_id_var.set("")
        rule_text_var.set("")

    rules_tree.bind("<<TreeviewSelect>>", on_rule_select)
    ttk.Button(tab_rules, text="Add", command=add_rule).grid(
        row=3, column=0, sticky="w"
    )
    ttk.Button(tab_rules, text="Update", command=update_rule).grid(
        row=3, column=1, sticky="w"
    )
    ttk.Button(tab_rules, text="Delete", command=del_rule).grid(
        row=3, column=2, sticky="w"
    )

    # ----- Sentinels Tab -----
    tab_s = ttk.Frame(nb)
    nb.add(tab_s, text="Sentinels")
    tab_s.grid_columnconfigure(1, weight=1)
    s_start = tk.StringVar(value=cfg["sentinels"]["start"])
    s_end = tk.StringVar(value=cfg["sentinels"]["end"])
    s_check = tk.StringVar(value=cfg["sentinels"]["self_check_line"])
    include_oc_var = tk.IntVar(
        value=1 if cfg.get("include_output_contract_in_prompts", True) else 0
    )
    r5_enforce_var = tk.IntVar(value=1 if cfg.get("r5", {}).get("enforce", True) else 0)

    ttk.Label(tab_s, text="Start marker").grid(row=0, column=0, sticky="w")
    e_s_start = ttk.Entry(tab_s, textvariable=s_start, width=60)
    e_s_start.grid(row=0, column=1, sticky="ew")
    ToolTip(
        e_s_start,
        text="Keep simple (e.g., '### FILE OUTPUT START  ###'). Validator also tolerates legacy '... START <anything> ###' style.",
    )

    ttk.Label(tab_s, text="End marker").grid(row=1, column=0, sticky="w")
    e_s_end = ttk.Entry(tab_s, textvariable=s_end, width=60)
    e_s_end.grid(row=1, column=1, sticky="ew")
    ToolTip(e_s_end, text="Marks the end of the model's file output to stop parsers.")

    ttk.Label(tab_s, text="Self-check line").grid(row=2, column=0, sticky="w")
    e_s_check = ttk.Entry(tab_s, textvariable=s_check, width=60)
    e_s_check.grid(row=2, column=1, sticky="ew")
    ToolTip(
        e_s_check, text="A short line the model must echo to prove it read the rules."
    )

    ttk.Checkbutton(
        tab_s, text="Include Output Contract in prompts", variable=include_oc_var
    ).grid(row=3, column=1, sticky="w")
    ttk.Checkbutton(
        tab_s, text="Enforce R5 in validator", variable=r5_enforce_var
    ).grid(row=4, column=1, sticky="w")

    # ----- Output Contract Tab -----
    tab_oc = ttk.Frame(nb)
    nb.add(tab_oc, text="Output Contract")
    tab_oc.grid_columnconfigure(1, weight=1)
    fb = cfg["output_contract"]["file_block"]
    fb_start = tk.StringVar(value=fb["start"])
    fb_end = tk.StringVar(value=fb["end"])
    fb_fields = tk.StringVar(value=", ".join(fb["fields"]))
    fb_example = tk.Text(tab_oc, height=7, wrap="word")
    fb_example.insert("1.0", fb.get("example", ""))

    ttk.Label(tab_oc, text="Block start").grid(row=0, column=0, sticky="w")
    e_fb_start = ttk.Entry(tab_oc, textvariable=fb_start)
    e_fb_start.grid(row=0, column=1, sticky="ew")
    ToolTip(e_fb_start, text=fb.get("help", {}).get("start", ""))

    ttk.Label(tab_oc, text="Block end").grid(row=1, column=0, sticky="w")
    e_fb_end = ttk.Entry(tab_oc, textvariable=fb_end)
    e_fb_end.grid(row=1, column=1, sticky="ew")
    ToolTip(e_fb_end, text=fb.get("help", {}).get("end", ""))

    ttk.Label(tab_oc, text="Fields (CSV)").grid(row=2, column=0, sticky="w")
    e_fb_fields = ttk.Entry(tab_oc, textvariable=fb_fields)
    e_fb_fields.grid(row=2, column=1, sticky="ew")
    ToolTip(e_fb_fields, text=fb.get("help", {}).get("fields", ""))

    ttk.Label(tab_oc, text="Example").grid(row=3, column=0, sticky="nw")
    fb_example.grid(row=3, column=1, sticky="nsew")
    ToolTip(fb_example, text=fb.get("help", {}).get("example", ""))

    # ----- Scenarios Tab -----
    tab_sc = ttk.Frame(nb)
    nb.add(tab_sc, text="Scenarios")
    tab_sc.grid_columnconfigure(2, weight=1)
    tab_sc.grid_rowconfigure(0, weight=1)
    sc_list = ttk.Treeview(
        tab_sc, columns=("key", "title", "desc"), show="headings", height=6
    )
    sc_list.heading("key", text="Key")
    sc_list.heading("title", text="Title")
    sc_list.heading("desc", text="Description")
    sc_list.grid(row=0, column=0, columnspan=3, sticky="nsew")

    sc_key = tk.StringVar()
    sc_title = tk.StringVar()
    sc_desc = tk.Text(tab_sc, height=4, wrap="word")
    ttk.Label(tab_sc, text="Key").grid(row=1, column=0, sticky="w")
    ttk.Entry(tab_sc, textvariable=sc_key).grid(row=1, column=1, sticky="ew")
    ttk.Label(tab_sc, text="Title").grid(row=2, column=0, sticky="w")
    ttk.Entry(tab_sc, textvariable=sc_title).grid(row=2, column=1, sticky="ew")
    ttk.Label(tab_sc, text="Description").grid(row=3, column=0, sticky="nw")
    sc_desc.grid(row=3, column=1, sticky="nsew")
    tab_sc.grid_rowconfigure(3, weight=1)

    sec_frame = ttk.Frame(tab_sc)
    sec_frame.grid(row=4, column=0, columnspan=3, sticky="nsew", pady=6)
    sec_tree = ttk.Treeview(
        sec_frame, columns=("label", "prompt"), show="headings", height=6
    )
    sec_tree.heading("label", text="Label")
    sec_tree.heading("prompt", text="Prompt")
    sec_tree.grid(row=0, column=0, columnspan=3, sticky="nsew")
    sec_frame.grid_columnconfigure(2, weight=1)
    sec_frame.grid_rowconfigure(0, weight=1)
    sec_label = tk.StringVar()
    sec_prompt = tk.StringVar()
    ttk.Label(sec_frame, text="Section Label").grid(row=1, column=0, sticky="w")
    ttk.Entry(sec_frame, textvariable=sec_label).grid(row=1, column=1, sticky="ew")
    ttk.Label(sec_frame, text="Section Prompt").grid(row=2, column=0, sticky="w")
    ttk.Entry(sec_frame, textvariable=sec_prompt).grid(row=2, column=1, sticky="ew")

    extra_directives_text = tk.Text(tab_sc, height=5, wrap="word")
    ttk.Label(tab_sc, text="Extra Directives (one per line)").grid(
        row=5, column=0, sticky="nw"
    )
    extra_directives_text.grid(row=5, column=1, sticky="nsew")

    def refresh_scenarios():
        sc_list.delete(*sc_list.get_children())
        for k, v in cfg["scenarios"].items():
            sc_list.insert(
                "",
                "end",
                iid=k,
                values=(
                    k,
                    v.get("title", ""),
                    v.get("description", "")[:80].replace("\n", " "),
                ),
            )

    def load_selected_scenario(_event=None):
        sel = sc_list.selection()
        if not sel:
            return
        k = sel[0]
        v = cfg["scenarios"][k]
        sc_key.set(k)
        sc_title.set(v.get("title", ""))
        sc_desc.delete("1.0", "end")
        sc_desc.insert("1.0", v.get("description", ""))
        sec_tree.delete(*sec_tree.get_children())
        for s in v.get("sections", []):
            sec_tree.insert("", "end", values=(s.get("label", ""), s.get("prompt", "")))
        extra_directives_text.delete("1.0", "end")
        for d in v.get("extra_directives", []):
            extra_directives_text.insert("end", d + "\n")

    def add_or_update_scenario():
        k = sc_key.get().strip()
        if not k:
            messagebox.showerror("Missing", "Scenario key required")
            return
        cfg["scenarios"].setdefault(
            k, {"title": "", "description": "", "sections": [], "extra_directives": []}
        )
        v = cfg["scenarios"][k]
        v["title"] = sc_title.get().strip()
        v["description"] = sc_desc.get("1.0", "end").strip()
        sections = []
        for item in sec_tree.get_children():
            lab, pr = sec_tree.item(item, "values")
            sections.append({"label": lab, "prompt": pr})
        v["sections"] = sections
        v["extra_directives"] = [
            ln.strip()
            for ln in extra_directives_text.get("1.0", "end").splitlines()
            if ln.strip()
        ]
        refresh_scenarios()

    def delete_scenario():
        sel = sc_list.selection()
        if not sel:
            return
        k = sel[0]
        if k in cfg["scenarios"]:
            del cfg["scenarios"][k]
            refresh_scenarios()

    def add_section():
        lab = sec_label.get().strip()
        pr = sec_prompt.get().strip()
        if not lab:
            messagebox.showerror("Missing", "Section label required")
            return
        sec_tree.insert("", "end", values=(lab, pr))

    def del_section():
        sel = sec_tree.selection()
        if sel:
            sec_tree.delete(sel[0])

    sc_list.bind("<<TreeviewSelect>>", load_selected_scenario)
    ttk.Button(tab_sc, text="Add/Update Scenario", command=add_or_update_scenario).grid(
        row=6, column=0, sticky="w"
    )
    ttk.Button(tab_sc, text="Delete Scenario", command=delete_scenario).grid(
        row=6, column=1, sticky="w"
    )
    ttk.Button(sec_frame, text="Add Section", command=add_section).grid(
        row=3, column=0, sticky="w"
    )
    ttk.Button(sec_frame, text="Delete Section", command=del_section).grid(
        row=3, column=1, sticky="w"
    )

    # ----- Help Tab -----
    tab_help = ttk.Frame(nb)
    nb.add(tab_help, text="Help")
    tab_help.grid_columnconfigure(2, weight=1)
    tab_help.grid_rowconfigure(0, weight=1)
    help_fields = cfg.setdefault("help", {}).setdefault(
        "fields", DEFAULT_CONFIG["help"]["fields"]
    )

    hf_list = ttk.Treeview(
        tab_help, columns=("field", "desc"), show="headings", height=6
    )
    hf_list.heading("field", text="Field")
    hf_list.heading("desc", text="Description")
    hf_list.grid(row=0, column=0, columnspan=3, sticky="nsew")

    hf_key = tk.StringVar()
    hf_desc = tk.Text(tab_help, height=4, wrap="word")
    ttk.Label(tab_help, text="Field").grid(row=1, column=0, sticky="w")
    ttk.Entry(tab_help, textvariable=hf_key).grid(row=1, column=1, sticky="ew")
    ttk.Label(tab_help, text="Description").grid(row=2, column=0, sticky="nw")
    hf_desc.grid(row=2, column=1, sticky="nsew")

    def refresh_help_lists():
        hf_list.delete(*hf_list.get_children())
        for k, v in help_fields.items():
            hf_list.insert("", "end", values=(k, v[:80].replace("\n", " ")))

    def load_selected_field(_event=None):
        sel = hf_list.selection()
        if not sel:
            return
        k, _ = hf_list.item(sel[0], "values")
        hf_key.set(k)
        hf_desc.delete("1.0", "end")
        hf_desc.insert("1.0", help_fields.get(k, ""))

    def save_field_help():
        k = hf_key.get().strip()
        if not k:
            messagebox.showerror("Missing", "Field name required")
            return
        help_fields[k] = hf_desc.get("1.0", "end").strip()
        refresh_help_lists()

    ttk.Button(tab_help, text="Save Field Help", command=save_field_help).grid(
        row=3, column=1, sticky="e"
    )
    hf_list.bind("<<TreeviewSelect>>", load_selected_field)

    # ----- Requirements Tab (CRUD + project mapping) -----
    tab_req = ttk.Frame(nb)
    nb.add(tab_req, text="Requirements")
    for c in range(4):
        tab_req.grid_columnconfigure(c, weight=1 if c == 1 else 0)
    for r in range(6):
        tab_req.grid_rowconfigure(r, weight=1 if r in (1, 4) else 0)

    ttk.Label(tab_req, text="Project Filter").grid(
        row=0, column=0, sticky="w", padx=4, pady=4
    )
    project_filter_var = tk.StringVar(value=cfg.get("project_name", ""))
    project_filter_entry = ttk.Entry(tab_req, textvariable=project_filter_var)
    project_filter_entry.grid(row=0, column=1, sticky="ew", padx=4, pady=4)

    # All requirements (global catalog)
    ttk.Label(tab_req, text="All Requirements (catalog)").grid(
        row=1, column=0, sticky="w", padx=4
    )
    req_catalog = ttk.Treeview(
        tab_req, columns=("id", "text", "tag"), show="headings", height=10
    )
    req_catalog.heading("id", text="ID")
    req_catalog.heading("text", text="Text")
    req_catalog.heading("tag", text="Tag")
    req_catalog.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=4, pady=4)

    # Project-mapped requirements with enabled flag
    ttk.Label(tab_req, text="Project Requirements (enabled flags)").grid(
        row=1, column=2, sticky="w", padx=4
    )
    project_req = ttk.Treeview(
        tab_req, columns=("id", "text", "tag", "enabled"), show="headings", height=10
    )
    project_req.heading("id", text="ID")
    project_req.heading("text", text="Text")
    project_req.heading("tag", text="Tag")
    project_req.heading("enabled", text="Enabled")
    project_req.grid(row=2, column=2, columnspan=2, sticky="nsew", padx=4, pady=4)

    # Editors
    req_text_var = tk.StringVar()
    req_tag_var = tk.StringVar()
    ttk.Label(tab_req, text="Text").grid(row=3, column=0, sticky="w", padx=4)
    ttk.Entry(tab_req, textvariable=req_text_var).grid(
        row=3, column=1, sticky="ew", padx=4
    )
    ttk.Label(tab_req, text="Tag").grid(row=3, column=2, sticky="w", padx=4)
    ttk.Entry(tab_req, textvariable=req_tag_var).grid(
        row=3, column=3, sticky="ew", padx=4
    )

    def refresh_req_tab():
        # catalog
        req_catalog.delete(*req_catalog.get_children())
        for rid, text, tag in req_list_all():
            req_catalog.insert(
                "", "end", iid=str(rid), values=(rid, text, tag if tag else "")
            )
        # project mapping
        project = project_filter_var.get().strip()
        project_req.delete(*project_req.get_children())
        if project:
            for rid, text, tag, en in req_list_all_with_project(project):
                project_req.insert(
                    "",
                    "end",
                    iid=f"{project}:{rid}",
                    values=(
                        rid,
                        text,
                        tag if tag else "",
                        "1" if int(en) == 1 else "0",
                    ),
                )

    def on_catalog_select(_evt=None):
        sel = req_catalog.selection()
        if not sel:
            return
        rid = int(sel[0])
        for _id, text, tag in req_list_all():
            if _id == rid:
                req_text_var.set(text)
                req_tag_var.set(tag or "")
                break

    def on_project_req_select(_evt=None):
        # sync editor with selected project requirement row
        sel = project_req.selection()
        if not sel:
            return
        _iid = sel[0]
        _rid = int(project_req.item(_iid, "values")[0])
        for rid, text, tag in req_list_all():
            if rid == _rid:
                req_text_var.set(text)
                req_tag_var.set(tag or "")
                break

    def add_requirement():
        text = req_text_var.get().strip()
        if not text:
            messagebox.showerror("Missing", "Requirement text is required.")
            return
        tag = req_tag_var.get().strip() or None
        rid = req_add(text, tag)
        refresh_req_tab()

    def update_requirement():
        sel = req_catalog.selection()
        if not sel:
            messagebox.showerror(
                "No Selection", "Select a requirement in the catalog to update."
            )
            return
        rid = int(sel[0])
        text = req_text_var.get().strip()
        if not text:
            messagebox.showerror("Missing", "Requirement text is required.")
            return
        tag = req_tag_var.get().strip() or None
        req_update(rid, text, tag)
        refresh_req_tab()

    def delete_requirement():
        sel = req_catalog.selection()
        if not sel:
            messagebox.showerror(
                "No Selection", "Select a requirement in the catalog to delete."
            )
            return
        rid = int(sel[0])
        if messagebox.askyesno(
            "Confirm", f"Delete requirement {rid}? This also removes project mappings."
        ):
            req_delete(rid)
            refresh_req_tab()

    def map_selected_to_project(enabled: bool):
        project = project_filter_var.get().strip()
        if not project:
            messagebox.showerror("No Project", "Enter a Project Filter first.")
            return
        sels = req_catalog.selection()
        if not sels:
            messagebox.showerror("No Selection", "Select requirements in the catalog.")
            return
        for s in sels:
            rid = int(s)
            req_set_for_project(project, rid, enabled)
        refresh_req_tab()

    def toggle_enable_on_project():
        project = project_filter_var.get().strip()
        if not project:
            messagebox.showerror("No Project", "Enter a Project Filter first.")
            return
        sels = project_req.selection()
        if not sels:
            messagebox.showerror(
                "No Selection", "Select project requirements to toggle."
            )
            return
        for s in sels:
            _rid = int(project_req.item(s, "values")[0])
            current = int(project_req.item(s, "values")[3])
            req_set_for_project(project, _rid, enabled=(current == 0))
        refresh_req_tab()

    # Buttons row
    btns = ttk.Frame(tab_req)
    btns.grid(row=5, column=0, columnspan=4, sticky="ew", padx=4, pady=4)
    ttk.Button(btns, text="Add Requirement", command=add_requirement).pack(
        side="left", padx=4
    )
    ttk.Button(btns, text="Update Requirement", command=update_requirement).pack(
        side="left", padx=4
    )
    ttk.Button(btns, text="Delete Requirement", command=delete_requirement).pack(
        side="left", padx=4
    )
    ttk.Button(
        btns,
        text="Map Selected → Project (Enabled)",
        command=lambda: map_selected_to_project(True),
    ).pack(side="left", padx=4)
    ttk.Button(
        btns,
        text="Map Selected → Project (Disabled)",
        command=lambda: map_selected_to_project(False),
    ).pack(side="left", padx=4)
    ttk.Button(
        btns, text="Toggle Enable (Project)", command=toggle_enable_on_project
    ).pack(side="left", padx=4)

    req_catalog.bind("<<TreeviewSelect>>", on_catalog_select)
    project_req.bind("<<TreeviewSelect>>", on_project_req_select)
    project_filter_var.trace_add("write", lambda *_: refresh_req_tab())

    # ----- Help Tab -----
    tab_help = tab_help  # already defined above

    # ----- History Tab -----
    tab_hist = ttk.Frame(nb)
    nb.add(tab_hist, text="History")
    tab_hist.grid_columnconfigure(3, weight=1)
    tab_hist.grid_rowconfigure(1, weight=1)

    hist_tree = ttk.Treeview(
        tab_hist,
        columns=("id", "created", "scenario", "task"),
        show="headings",
        height=10,
    )
    hist_tree.heading("id", text="ID")
    hist_tree.heading("created", text="Created (UTC)")
    hist_tree.heading("scenario", text="Scenario")
    hist_tree.heading("task", text="Task")
    hist_tree.grid(row=0, column=0, columnspan=4, sticky="nsew")

    hist_preview = tk.Text(tab_hist, height=12, wrap="word")
    hist_preview.grid(row=1, column=0, columnspan=4, sticky="nsew")

    def refresh_history():
        hist_tree.delete(*hist_tree.get_children())
        for pid, created, scen, task in list_prompts():
            hist_tree.insert(
                "", "end", iid=str(pid), values=(pid, created, scen, task[:160])
            )

    def load_selected_prompt(_event=None):
        sel = hist_tree.selection()
        if not sel:
            return
        pid = int(sel[0])
        content = get_prompt_content(pid) or ""
        hist_preview.delete("1.0", "end")
        hist_preview.insert("1.0", content)

    def export_selected_prompt():
        sel = hist_tree.selection()
        if not sel:
            return
        pid = int(sel[0])
        content = get_prompt_content(pid) or ""
        if not content:
            return
        ensure_app_dirs()
        out_path = os.path.join(OUTPUT_DIR, f"prompt_saved_{pid}_{now_stamp()}.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
        messagebox.showinfo("Exported", f"Prompt exported to {out_path}")

    def retrieve_selected_to_prompt():
        sel = hist_tree.selection()
        if not sel:
            messagebox.showerror("No Selection", "Select a row in History first.")
            return
        pid = int(sel[0])
        content = get_prompt_content(pid) or ""
        vals = hist_tree.item(sel[0], "values")
        _, _, scen, task = (
            vals if len(vals) == 4 else (pid, "", scenario_var.get(), task_var.get())
        )

        nb.select(tab_prompt)
        try:
            scenario_var.set(scen)
        except Exception:
            pass
        rebuild_sections()

        task_parsed, sections_map = parse_prompt_to_fields(
            cfg, scenario_var.get(), content
        )
        task_var.set(task_parsed or task)
        for label, widget in section_widgets.items():
            widget.delete("1.0", "end")
            widget.insert("1.0", sections_map.get(label, ""))

        output.delete("1.0", "end")
        output.insert("1.0", content)

    ttk.Button(tab_hist, text="Refresh", command=refresh_history).grid(
        row=2, column=0, sticky="w"
    )
    ttk.Button(tab_hist, text="Export Selected", command=export_selected_prompt).grid(
        row=2, column=1, sticky="w"
    )
    ttk.Button(
        tab_hist, text="Retrieve to Prompt", command=retrieve_selected_to_prompt
    ).grid(row=2, column=2, sticky="w")

    def on_tab_changed(_event=None):
        try:
            current = nb.tab(nb.select(), "text")
            if current == "History":
                refresh_history()
        except Exception:
            pass

    nb.bind("<<NotebookTabChanged>>", on_tab_changed)

    # ----- Validate Tab -----
    tab_val = ttk.Frame(nb)
    nb.add(tab_val, text="Validate")
    tab_val.grid_columnconfigure(1, weight=1)
    tab_val.grid_rowconfigure(1, weight=1)

    ttk.Label(tab_val, text="Paste model reply below; then click Validate").grid(
        row=0, column=0, sticky="w", padx=2, pady=2
    )
    reply_text = tk.Text(tab_val, height=16, wrap="word")
    reply_text.grid(row=1, column=0, columnspan=6, sticky="nsew", padx=2, pady=2)

    val_tree = ttk.Treeview(
        tab_val,
        columns=("path", "language", "lines", "sha256", "r5"),
        show="headings",
        height=8,
    )
    val_tree.heading("path", text="path")
    val_tree.heading("language", text="language")
    val_tree.heading("lines", text="lines")
    val_tree.heading("sha256", text="sha256")
    val_tree.heading("r5", text="R5")
    val_tree.grid(row=2, column=0, columnspan=6, sticky="nsew", padx=2, pady=4)
    tab_val.grid_rowconfigure(2, weight=1)

    file_preview = tk.Text(tab_val, height=12, wrap="none")
    file_preview.grid(row=3, column=0, columnspan=6, sticky="nsew", padx=2, pady=2)

    status_lbl = ttk.Label(tab_val, text="Status: idle")
    status_lbl.grid(row=4, column=0, columnspan=6, sticky="w", padx=2, pady=2)

    parsed_cache: Dict[str, Any] = {"files": []}

    def build_validation_report(parsed: Dict[str, Any]) -> str:
        lines = []
        lines.append("PromptForge Validation Report")
        lines.append(
            f"Time: {datetime.datetime.utcnow().isoformat(timespec='seconds')}Z"
        )
        lines.append("")
        lines.append(
            f"Self-check: {'OK' if parsed.get('has_self_check') else 'missing'}"
        )
        lines.append(
            f"Start sentinel: {'OK' if parsed.get('has_start') else 'missing'}"
        )
        lines.append(f"End sentinel: {'OK' if parsed.get('has_end') else 'missing'}")
        errs = parsed.get("errors") or []
        if errs:
            lines.append("Errors:")
            for e in errs:
                lines.append(f"- {e}")
        files = parsed.get("files") or []
        lines.append("")
        lines.append(f"Files parsed: {len(files)}")
        for f in files:
            r5 = f.get("r5") or {}
            r5s = (
                "OK"
                if r5.get("ok", True)
                else "issues: " + "; ".join(r5.get("issues", []))
            )
            lines.append(
                f"- path={f['path']} | language={f['language']} | lines={f['lines']} | sha256={f['sha256']} | R5={r5s}"
            )
        lines.append("")
        lines.append("Fences required (from Output Contract):")
        fb = cfg["output_contract"]["file_block"]
        lines.append(f"  start fence: {fb['start']}")
        lines.append(f"  end fence:   {fb['end']}")
        lines.append("  required headers: " + ", ".join(fb["fields"]))
        return "\n".join(lines)

    def validate_click():
        harvest_all()
        raw = reply_text.get("1.0", "end")
        parsed = parse_ai_reply(cfg, raw)
        parsed_cache.clear()
        parsed_cache.update(parsed)
        val_tree.delete(*val_tree.get_children())
        for f in parsed.get("files", []):
            r5 = f.get("r5")
            r5s = "OK" if (not r5 or r5.get("ok", True)) else "issues"
            val_tree.insert(
                "",
                "end",
                iid=f["path"],
                values=(f["path"], f["language"], f["lines"], f["sha256"], r5s),
            )
        msgs = []
        msgs.append("self_check=" + ("OK" if parsed["has_self_check"] else "missing"))
        msgs.append("start=" + ("OK" if parsed["has_start"] else "missing"))
        msgs.append("end=" + ("OK" if parsed["has_end"] else "missing"))
        if parsed.get("errors"):
            msgs.append("errors=" + "; ".join(parsed["errors"]))
        status_lbl.config(text="Status: " + " | ".join(msgs))

    def on_val_select(_evt=None):
        sel = val_tree.selection()
        if not sel:
            return
        path = sel[0]
        for f in parsed_cache.get("files", []):
            if f["path"] == path:
                file_preview.delete("1.0", "end")
                file_preview.insert("1.0", f["contents"])
                break

    def save_selected_click():
        sel = val_tree.selection()
        if not sel:
            messagebox.showerror("No Selection", "Select a file in the grid first.")
            return
        ensure_app_dirs()
        base = filedialog.askdirectory(title="Choose destination folder (project root)")
        if not base:
            return
        for iid in sel:
            for f in parsed_cache.get("files", []):
                if f["path"] == iid:
                    absdir = os.path.join(base, os.path.dirname(f["path"]))
                    os.makedirs(absdir, exist_ok=True)
                    with open(
                        os.path.join(base, f["path"]), "w", encoding="utf-8"
                    ) as out:
                        out.write(f["contents"])
        messagebox.showinfo("Saved", "Selected file(s) saved.")

    def save_all_click():
        ensure_app_dirs()
        base = filedialog.askdirectory(title="Choose destination folder (project root)")
        if not base:
            return
        save_parsed_files_to_folder(parsed_cache, base)
        messagebox.showinfo("Saved", "All files saved.")

    def export_zip_click():
        ensure_app_dirs()
        path = filedialog.asksaveasfilename(
            defaultextension=".zip", filetypes=[("Zip", "*.zip")]
        )
        if not path:
            return
        export_parsed_to_zip(parsed_cache, path)
        messagebox.showinfo("Exported", f"ZIP written to {path}")

    def copy_status_click():
        report = build_validation_report(parsed_cache)
        try:
            root.clipboard_clear()
            root.clipboard_append(report)
            messagebox.showinfo("Copied", "Validation report copied to clipboard.")
        except Exception as e:
            messagebox.showerror("Clipboard Error", str(e))

    ttk.Button(tab_val, text="Validate", command=validate_click).grid(
        row=5, column=0, sticky="w", padx=2, pady=4
    )
    ttk.Button(
        tab_val, text="Save Selected to Project", command=save_selected_click
    ).grid(row=5, column=1, sticky="w", padx=2, pady=4)
    ttk.Button(tab_val, text="Save All to Project", command=save_all_click).grid(
        row=5, column=2, sticky="w", padx=2, pady=4
    )
    ttk.Button(tab_val, text="Export ZIP", command=export_zip_click).grid(
        row=5, column=3, sticky="w", padx=2, pady=4
    )
    ttk.Button(tab_val, text="Copy Status", command=copy_status_click).grid(
        row=5, column=4, sticky="w", padx=2, pady=4
    )

    val_tree.bind("<<TreeviewSelect>>", on_val_select)

    # finish setup
    refresh_rules()
    refresh_scenarios()
    rebuild_sections()
    refresh_help_lists()
    refresh_history()
    refresh_rules_selector()
    refresh_req_selector()
    refresh_req_tab()

    def on_close():
        try:
            harvest_all()
            save_config(cfg)
        finally:
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "gui":
        run_gui()
        return
    args = parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

# line-count footer (R5)
# lines: 1250
