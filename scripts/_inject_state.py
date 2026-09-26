#!/usr/bin/env python3
"""
_inject_state.py
Reads review_state.json and injects it as an inline JS variable into visualizer/index.html
so the visualizer works when opened directly as a file:// URL (no server needed).

Re-running this script replaces any previously injected state (idempotent).
Run from repo root: python scripts/_inject_state.py
"""
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
STATE_PATH = REPO / "review_state.json"
HTML_PATH  = REPO / "visualizer" / "index.html"

# ---------------------------------------------------------------------------
# Markers used to locate / delimit the injected block
# ---------------------------------------------------------------------------
# What we insert before loadState():
#   const INLINE_STATE = {...};
#
#   async function loadState() {
#     // Use inline embedded state first ...
#     if (typeof INLINE_STATE !== 'undefined' ...) { ... }
#
#     // Try fetching ...

CLEAN_MARKER     = "async function loadState() {"          # present in the clean (non-injected) file
INLINE_BRANCH_START = "  // Use inline embedded state first"
FETCH_MARKER     = "  // Try fetching ../review_state.json (relative to visualizer/)"

# ---------------------------------------------------------------------------
state_text = STATE_PATH.read_text(encoding="utf-8")
try:
    json.loads(state_text)
except json.JSONDecodeError as e:
    print(f"ERROR: review_state.json is not valid JSON: {e}", file=sys.stderr)
    sys.exit(1)

html = HTML_PATH.read_text(encoding="utf-8")

# ── Step 1: Strip any previously injected INLINE_STATE declaration ──────────
# Pattern: everything from "const INLINE_STATE = " up to the newline before
# "async function loadState() {"
html = re.sub(
    r"const INLINE_STATE = \{.*?\};\s*\n\n(?=async function loadState)",
    "",
    html,
    count=1,
    flags=re.DOTALL,
)

# ── Step 2: Strip any previously injected inline-first branch inside loadState ──
# Covers the 5-line block we add inside the function body
html = re.sub(
    r"  // Use inline embedded state first.*?  }\n\n  ",
    "  ",
    html,
    count=1,
    flags=re.DOTALL,
)

# ── Step 3: Verify clean marker exists ──────────────────────────────────────
if CLEAN_MARKER not in html:
    print("ERROR: could not find 'async function loadState()' in index.html", file=sys.stderr)
    sys.exit(1)

if FETCH_MARKER not in html:
    print("ERROR: could not find fetch marker inside loadState()", file=sys.stderr)
    sys.exit(1)

# ── Step 4: Inject INLINE_STATE before loadState ────────────────────────────
INJECTED_DECL = f"const INLINE_STATE = {state_text};\n\nasync function loadState() {{"
html = html.replace(CLEAN_MARKER, INJECTED_DECL, 1)

# ── Step 5: Inject inline-first branch inside loadState ─────────────────────
INLINE_BRANCH = (
    "  // Use inline embedded state first — works with file:// (no server needed)\n"
    "  if (typeof INLINE_STATE !== 'undefined' && INLINE_STATE && INLINE_STATE.nodes) {\n"
    "    buildGraph(INLINE_STATE);\n"
    "    return;\n"
    "  }\n\n  "
)
html = html.replace(FETCH_MARKER, INLINE_BRANCH + FETCH_MARKER, 1)

# ── Write ────────────────────────────────────────────────────────────────────
HTML_PATH.write_text(html, encoding="utf-8")
print(f"Done. index.html updated ({len(html):,} chars). Open visualizer/index.html directly in a browser.")
