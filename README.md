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
├── .bob/
│   └── custom_modes.yaml  # Bob custom mode: review-coach
├── scripts/
│   └── review_pr.sh       # Trigger script for PR-based review
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
4. A shell script (`scripts/review_pr.sh`) or the `review-coach` Bob custom mode
   can be used to trigger the flow on any new PR or code diff.

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
