#!/usr/bin/env python3
"""
update_state.py — IBM Bob AI Code Review Coach
Re-reads findings_*.md files in the repo root and regenerates review_state.json.

Run this after any IBM Bob review session to refresh the graph with the latest findings.
It preserves the "status" field of any node that already exists in review_state.json
so that manually marked "in_progress" or "resolved" items are not reset.

Usage:
    python scripts/update_state.py
    python scripts/update_state.py --repo-root /path/to/repo
"""

import json
import os
import re
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r'^###\s+((?:SEC|QUA|TST|DOC)-\d+):\s+(.+)$')
_FILE_RE = re.compile(r'\*\*File:\*\*\s+`(.+?)`')
_ISSUE_RE = re.compile(r'\*\*Issue:\*\*\s+(.+)')
_FIX_RE = re.compile(r'\*\*Fix:\*\*\s+(.+)')
_SECTION_RE = re.compile(r'^##\s+(CRITICAL|HIGH|MEDIUM|LOW)$')

# For findings_tests.md and findings_docs.md which use table rows
_TABLE_ROW_RE = re.compile(r'^\|\s*`?([^`|]+)`?\s*\|\s*([^|]+)\|\s*([^|]+)\|')

_SEVERITY_MAP = {
    "CRITICAL": "critical",
    "HIGH": "high",
    "MEDIUM": "medium",
    "LOW": "low",
}


# Counter for synthetic IDs for TST/DOC table entries
_ID_COUNTERS: dict[str, int] = {}


def _next_id(prefix: str) -> str:
    _ID_COUNTERS[prefix] = _ID_COUNTERS.get(prefix, 0) + 1
    return f"{prefix}-{_ID_COUNTERS[prefix]:03d}"


def _parse_findings_file(path: Path) -> list[dict]:
    """Parse a findings_*.md file and return a list of finding dicts."""
    findings = []
    current_severity = "medium"
    current = {}

    def _flush(c):
        if c.get("id"):
            findings.append(c)

    # Detect prefix from filename (e.g. findings_tests.md -> TST)
    stem = path.stem  # e.g. "findings_tests"
    prefix_map = {"findings_security": "SEC", "findings_quality": "QUA",
                  "findings_tests": "TST", "findings_docs": "DOC"}
    file_prefix = prefix_map.get(stem, "UNK")

    lines = path.read_text(encoding="utf-8").splitlines()
    in_table = False
    table_header_seen = False

    for line in lines:
        stripped = line.strip()

        section_m = _SECTION_RE.match(stripped)
        if section_m:
            current_severity = _SEVERITY_MAP[section_m.group(1)]
            in_table = False
            continue

        heading_m = _HEADING_RE.match(stripped)
        if heading_m:
            _flush(current)
            current = {
                "id": heading_m.group(1),
                "raw_title": heading_m.group(2).strip(),
                "severity": current_severity,
                "status": "flagged",
                "file": "",
                "details": "",
                "fix": "",
            }
            in_table = False
            continue

        # Detect markdown table header separator (|---|---|)
        if stripped.startswith("|---") or stripped.startswith("| ---"):
            table_header_seen = True
            in_table = True
            continue

        # Table data rows (for findings_tests.md / findings_docs.md)
        if in_table and stripped.startswith("|"):
            parts = [p.strip().strip("`") for p in stripped.split("|") if p.strip()]
            if len(parts) >= 2 and parts[0] not in ("Function", "File", "Notes", "Severity"):
                func_name = parts[0]
                file_name = parts[1] if len(parts) > 1 else ""
                note_or_sev = parts[2] if len(parts) > 2 else ""
                # Map severity text
                sev = "medium"
                sev_lower = note_or_sev.lower()
                if "high" in sev_lower:
                    sev = "high"
                elif "critical" in sev_lower:
                    sev = "critical"
                elif "low" in sev_lower:
                    sev = "low"
                _flush(current)
                current = {
                    "id": _next_id(file_prefix),
                    "raw_title": func_name,
                    "severity": sev,
                    "status": "in_progress",  # table entries = partially addressed
                    "file": file_name,
                    "details": note_or_sev if file_prefix == "TST" else f"Missing docstring on `{func_name}` in {file_name}.",
                    "fix": (
                        f"Add unit tests for `{func_name}` (see sample_app/tests/test_services.py)."
                        if file_prefix == "TST"
                        else f"Apply Google-style docstring from {file_name.replace('.py','_documented.py')} to `{func_name}`."
                    ),
                }
            continue

        file_m = _FILE_RE.search(line)
        if file_m and current:
            current["file"] = file_m.group(1)
            continue

        issue_m = _ISSUE_RE.search(line)
        if issue_m and current:
            current["details"] = issue_m.group(1).strip()
            continue

        fix_m = _FIX_RE.search(line)
        if fix_m and current:
            current["fix"] = fix_m.group(1).strip()
            continue

    _flush(current)
    return findings


def _finding_to_node(f: dict) -> dict:
    """Convert a parsed finding dict to a graph node."""
    # Short label: ID + first ~25 chars of title
    short_title = f["raw_title"]
    if len(short_title) > 28:
        short_title = short_title[:26] + "…"
    label = f"{f['id']}\n{short_title}"

    return {
        "id": f["id"],
        "label": label,
        "type": "finding",
        "severity": f["severity"],
        "status": f["status"],
        "file": f["file"],
        "details": f["details"],
        "fix": f["fix"],
    }


# ---------------------------------------------------------------------------
# Branch meta nodes
# ---------------------------------------------------------------------------

_BRANCHES = {
    "SEC": {
        "id": "branch_security",
        "label_prefix": "Security",
        "type": "branch",
        "details": "Security vulnerabilities scanned by IBM Bob security subagent.",
        "fix": "Start with CRITICAL findings, then HIGH, MEDIUM, LOW.",
    },
    "QUA": {
        "id": "branch_quality",
        "label_prefix": "Code Quality",
        "type": "branch",
        "details": "Code quality issues flagged by IBM Bob quality subagent.",
        "fix": "Merge duplicated functions first — they have the highest maintenance cost.",
    },
    "TST": {
        "id": "branch_tests",
        "label_prefix": "Test Coverage",
        "type": "branch",
        "details": "Test coverage gaps identified by IBM Bob test subagent.",
        "fix": "Run: cd sample_app && python -m pytest tests/ --cov=src",
    },
    "DOC": {
        "id": "branch_docs",
        "label_prefix": "Documentation",
        "type": "branch",
        "details": "Documentation gaps identified by IBM Bob docs subagent.",
        "fix": "Apply generated docstrings from *_documented.py back to the originals.",
    },
}


def _prefix(node_id: str) -> str:
    return node_id.split("-")[0]


# ---------------------------------------------------------------------------
# Status preservation
# ---------------------------------------------------------------------------

def _load_existing_statuses(state_path: Path) -> dict[str, str]:
    """Return {node_id: status} from existing review_state.json, or {}."""
    if not state_path.exists():
        return {}
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
        return {n["id"]: n["status"] for n in data.get("nodes", [])}
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build_state(repo_root: Path) -> dict:
    state_path = repo_root / "review_state.json"
    existing_statuses = _load_existing_statuses(state_path)

    # Parse all four findings files
    findings_map: dict[str, list[dict]] = {}
    file_map = {
        "SEC": repo_root / "findings_security.md",
        "QUA": repo_root / "findings_quality.md",
        "TST": repo_root / "findings_tests.md",
        "DOC": repo_root / "findings_docs.md",
    }

    all_findings: list[dict] = []
    for prefix, path in file_map.items():
        if not path.exists():
            print(f"  WARNING: {path.name} not found — skipping {prefix} findings", file=sys.stderr)
            findings_map[prefix] = []
            continue
        found = _parse_findings_file(path)
        # Restore preserved statuses
        for f in found:
            if f["id"] in existing_statuses:
                f["status"] = existing_statuses[f["id"]]
        findings_map[prefix] = found
        all_findings.extend(found)
        print(f"  Parsed {len(found):>2} findings from {path.name}")

    # Build branch counts
    branch_counts = {p: len(v) for p, v in findings_map.items()}

    # Determine branch statuses
    def _branch_status(prefix):
        items = findings_map[prefix]
        if not items:
            return "resolved"
        statuses = {f["status"] for f in items}
        if statuses == {"resolved"}:
            return "resolved"
        if "in_progress" in statuses:
            return "in_progress"
        return "flagged"

    # Build node list
    nodes = []

    # Root
    total = len(all_findings)
    open_count = sum(1 for f in all_findings if f["status"] == "flagged")
    inprog_count = sum(1 for f in all_findings if f["status"] == "in_progress")
    resolved_count = sum(1 for f in all_findings if f["status"] == "resolved")

    root_status = "flagged"
    if resolved_count == total:
        root_status = "resolved"
    elif inprog_count > 0:
        root_status = "in_progress"

    nodes.append({
        "id": "root",
        "label": "ibm-bob-review-coach",
        "type": "root",
        "status": root_status,
        "details": (
            f"Sample Flask/Python application reviewed by IBM Bob AI Code Review Coach. "
            f"{total} total findings: {open_count} flagged, {inprog_count} in_progress, "
            f"{resolved_count} resolved."
        ),
        "fix": "Work through findings by priority: Critical first, then High, Medium, Low.",
    })

    # Branches
    branch_label_map = {
        "SEC": f"Security\n{branch_counts['SEC']} findings",
        "QUA": f"Code Quality\n{branch_counts['QUA']} findings",
        "TST": f"Test Coverage\n{branch_counts['TST']} findings",
        "DOC": f"Documentation\n{branch_counts['DOC']} findings",
    }
    for prefix, meta in _BRANCHES.items():
        b_status = _branch_status(prefix)
        if meta["id"] in existing_statuses:
            b_status = existing_statuses[meta["id"]]
        nodes.append({
            "id": meta["id"],
            "label": branch_label_map[prefix],
            "type": "branch",
            "status": b_status,
            "details": meta["details"],
            "fix": meta["fix"],
        })

    # Leaf finding nodes
    for f in all_findings:
        nodes.append(_finding_to_node(f))

    # Build edges
    edges = []
    branch_id_map = {p: _BRANCHES[p]["id"] for p in _BRANCHES}

    edges.append({"from": "root", "to": "branch_security"})
    edges.append({"from": "root", "to": "branch_quality"})
    edges.append({"from": "root", "to": "branch_tests"})
    edges.append({"from": "root", "to": "branch_docs"})

    for f in all_findings:
        p = _prefix(f["id"])
        if p in branch_id_map:
            edges.append({"from": branch_id_map[p], "to": f["id"]})

    # Assemble final state
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    state = {
        "meta": {
            "project": "ibm-bob-review-coach",
            "repo": "https://github.com/Pavankumar-p-k/ibm-bob-review-coach",
            "generated_by": "IBM Bob AI Code Review Coach — update_state.py",
            "last_updated": now,
            "total_findings": total,
            "open": open_count,
            "in_progress": inprog_count,
            "resolved": resolved_count,
        },
        "nodes": nodes,
        "edges": edges,
    }
    return state


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Regenerate review_state.json from findings_*.md files.")
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Path to repo root. Defaults to the parent of this script's directory.",
    )
    args = parser.parse_args()

    if args.repo_root:
        repo_root = Path(args.repo_root).resolve()
    else:
        repo_root = Path(__file__).resolve().parent.parent

    print(f"Repo root : {repo_root}")
    print(f"Reading findings files…")

    state = build_state(repo_root)

    out_path = repo_root / "review_state.json"
    out_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

    m = state["meta"]
    print(f"\nWrote {out_path}")
    print(f"  Nodes  : {len(state['nodes'])} ({m['total_findings']} findings + root + 4 branches)")
    print(f"  Edges  : {len(state['edges'])}")
    print(f"  Status : {m['open']} flagged / {m['in_progress']} in_progress / {m['resolved']} resolved")
    print(f"  Updated: {m['last_updated']}")


if __name__ == "__main__":
    main()
