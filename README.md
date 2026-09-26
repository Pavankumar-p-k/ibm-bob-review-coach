# IBM Bob AI Code Review Coach

An AI-powered code review coach built for the **IBM Bob 2.0 Hackathon**.  
IBM Bob IDE is the core engine — every review task runs as a tracked Bob session.

## Project Structure

```
ibm-bob-review-coach/
├── bob_sessions/          # Bob session screenshots (add manually after each task)
├── sample_app/
│   ├── src/               # Sample Python application (intentional vulns for demo)
│   │   ├── user_service.py
│   │   ├── order_service.py
│   │   └── api.py
│   ├── tests/             # Generated unit tests
│   └── requirements.txt
├── visualizer/
│   └── index.html         # Live node-graph visualizer (open in browser)
├── .bob/
│   └── custom_modes.yaml  # Bob custom mode: review-coach
├── scripts/
│   ├── review_pr.sh       # Trigger script for PR-based review
│   └── update_state.py    # Regenerates review_state.json from findings_*.md
├── review_state.json      # Live graph state: nodes + edges + status for every finding
├── REVIEW_SUMMARY.md      # Combined prioritized review findings
└── README.md
```

## How It Works

1. **IBM Bob** runs four parallel subagent sessions — one each for:
   - Security scanning
   - Code quality analysis
   - Test coverage gaps + test generation
   - Documentation gaps + docstring generation
2. Each session is tracked independently in Bob so usage can be screenshotted.
3. All findings are merged into `REVIEW_SUMMARY.md` with critical/high/medium/low priority.
4. `review_state.json` is generated/updated by `scripts/update_state.py` — it is the
   live graph state file that the visualizer reads and any AI agent can open to get instant context.
5. A shell script (`scripts/review_pr.sh`) or the `review-coach` Bob custom mode
   can be used to trigger the flow on any new PR or code diff.

## Live Node-Graph Visualizer

`visualizer/index.html` renders `review_state.json` as an **interactive mind-map** using
[vis-network](https://visjs.github.io/vis-network/) — no build step, just open in a browser.

### Open it

```bash
# Option 1 — simple Python server (recommended, enables fetch() for review_state.json)
cd ibm-bob-review-coach
python -m http.server 8080
# then open http://localhost:8080/visualizer/
```

```bash
# Option 2 — VS Code Live Server, npx serve, or any static file server
npx serve . -p 8080
```

### Features
- **Draggable nodes** — rearrange the graph freely
- **Click any node** — sidebar shows the issue description, file/line, and suggested fix
- **Color-coded by severity** — red (critical) → orange (high) → yellow (medium) → green (low)
- **Status toggle** — mark any finding Flagged / In Progress / Resolved directly in the UI
- **Persisted locally** — status changes are saved to `localStorage` (survive page refresh)
- **Stats bar** — live count of findings by severity and status at the top

### Updating the graph after a new Bob session

After any IBM Bob review session produces new findings, run:

```bash
python scripts/update_state.py
```

This re-parses all `findings_*.md` files and regenerates `review_state.json`.
Status values you manually set to "resolved" or "in_progress" are **preserved** across runs.

---

## Why review_state.json Solves AI Session Context Loss

Every AI coding session starts fresh — with no memory of what was flagged last time,
what's already being fixed, or what to pick up next. `review_state.json` is the answer.

It is a **single machine-readable file** that captures the complete review graph:
every finding, its severity, its current status (flagged / in_progress / resolved),
the file and line it lives in, and the suggested fix. Any AI agent — or a human teammate
— can open this file at the start of a session and immediately know:

- ✅ **What's resolved** — don't re-report or re-fix
- 🟡 **What's in progress** — continue from where the last session stopped
- 🔴 **What's still flagged** — the next priorities, ordered by severity

This solves the classic "context loss between AI coding sessions" problem:
instead of re-running the full review from scratch every time, the agent reads
`review_state.json`, picks the highest-priority unresolved finding, and gets to work.
The graph is the shared memory between sessions.

---

## Triggering a Review

### Via Script
```bash
bash scripts/review_pr.sh <path-to-code-or-diff>
```

### Via Bob Custom Mode
Open IBM Bob → switch to **review-coach** mode → describe the PR or paste a diff.

## Bob Sessions

Screenshots of each Bob session's consumption summary are stored in `bob_sessions/`.  
Add a screenshot after completing each of the four review tasks.

## Sample Application

`sample_app/src/` contains intentional vulnerabilities and code smells specifically
designed to exercise all four review dimensions. No real user data, company data,
or personally identifiable information is used — all code is synthetic sample data
with no commercial-use restrictions.

## Hackathon Compliance

- ✅ IBM Bob IDE is the core, visible orchestration engine
- ✅ No client data, PII, or social-media data used
- ✅ All sample code is synthetic/public-domain
- ✅ Per-task Bob session screenshots tracked in `bob_sessions/`
- ✅ Incremental git commits after every meaningful step
