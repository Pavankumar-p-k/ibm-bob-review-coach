#!/usr/bin/env bash
# =============================================================================
# review_pr.sh — IBM Bob AI Code Review Coach
# Trigger a full four-dimension code review on a PR diff or local path.
#
# Usage:
#   bash scripts/review_pr.sh [target]
#
#   target  Optional path to a Python file, directory, or unified diff file.
#           Defaults to sample_app/src/ when omitted.
#
# What it does:
#   1. Resolves the target and prints a header.
#   2. Runs bandit (security scan) on Python source files.
#   3. Runs pylint (quality / complexity) on Python source files.
#   4. Runs pytest --cov (test coverage) in sample_app/.
#   5. Checks for missing docstrings using pydocstyle.
#   6. Appends a timestamped summary section to REVIEW_SUMMARY.md.
#
# Prerequisites (install once):
#   pip install bandit pylint pytest pytest-cov pydocstyle
#
# IBM Bob integration:
#   This script is designed to be invoked from within IBM Bob's terminal,
#   or called automatically by a GitHub Actions workflow on every PR.
#   Each run appends results to REVIEW_SUMMARY.md so Bob sessions can
#   inspect the latest findings without re-running the full analysis.
# =============================================================================

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET="${1:-$REPO_ROOT/sample_app/src}"
SUMMARY_FILE="$REPO_ROOT/REVIEW_SUMMARY.md"
TIMESTAMP="$(date -u '+%Y-%m-%d %H:%M UTC')"
EXIT_CODE=0

# ── Helpers ───────────────────────────────────────────────────────────────────
header()  { echo; echo "══════════════════════════════════════════════"; echo "  $1"; echo "══════════════════════════════════════════════"; }
success() { echo "  ✅  $1"; }
warning() { echo "  ⚠️   $1"; }
fail()    { echo "  ❌  $1"; EXIT_CODE=1; }

# ── Banner ────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║   IBM Bob AI Code Review Coach                   ║"
echo "║   PR / Diff Review Runner                        ║"
echo "╚══════════════════════════════════════════════════╝"
echo "  Target : $TARGET"
echo "  Time   : $TIMESTAMP"

# Collect Python files from target
if [[ -f "$TARGET" && "$TARGET" == *.py ]]; then
  PY_FILES="$TARGET"
  PY_DIR="$(dirname "$TARGET")"
elif [[ -d "$TARGET" ]]; then
  PY_FILES=$(find "$TARGET" -name "*.py" ! -name "*_documented.py" | tr '\n' ' ')
  PY_DIR="$TARGET"
else
  warning "Target is not a Python file or directory — skipping static analysis."
  PY_FILES=""
  PY_DIR=""
fi

# ── 1. Security (bandit) ──────────────────────────────────────────────────────
header "STEP 1 / 4 — Security Scan (bandit)"
if command -v bandit &>/dev/null && [[ -n "$PY_FILES" ]]; then
  BANDIT_OUT=$(bandit -r "$PY_DIR" --severity-level medium -f text 2>&1 || true)
  echo "$BANDIT_OUT"
  HIGH_COUNT=$(echo "$BANDIT_OUT" | grep -c "Severity: High" || true)
  MED_COUNT=$(echo "$BANDIT_OUT"  | grep -c "Severity: Medium" || true)
  if [[ "$HIGH_COUNT" -gt 0 ]]; then
    fail "bandit: $HIGH_COUNT HIGH-severity issue(s) found"
  else
    success "bandit: no HIGH-severity issues detected ($MED_COUNT MEDIUM)"
  fi
else
  warning "bandit not installed or no Python files found — skipping. (pip install bandit)"
fi

# ── 2. Code Quality (pylint) ──────────────────────────────────────────────────
header "STEP 2 / 4 — Code Quality (pylint)"
if command -v pylint &>/dev/null && [[ -n "$PY_FILES" ]]; then
  PYLINT_OUT=$(pylint $PY_FILES --disable=C0114,C0115,C0116,W0611 --output-format=text 2>&1 || true)
  PYLINT_SCORE=$(echo "$PYLINT_OUT" | grep "Your code has been rated" | grep -oP '[0-9]+\.[0-9]+/10' || echo "n/a")
  echo "$PYLINT_OUT"
  success "pylint score: $PYLINT_SCORE"
else
  warning "pylint not installed or no Python files found — skipping. (pip install pylint)"
fi

# ── 3. Test Coverage (pytest) ─────────────────────────────────────────────────
header "STEP 3 / 4 — Test Coverage (pytest --cov)"
TESTS_DIR="$REPO_ROOT/sample_app/tests"
if command -v pytest &>/dev/null && [[ -d "$TESTS_DIR" ]]; then
  PYTEST_OUT=$(cd "$REPO_ROOT/sample_app" && python -m pytest tests/ --cov=src --cov-report=term-missing -q 2>&1 || true)
  echo "$PYTEST_OUT"
  FAIL_COUNT=$(echo "$PYTEST_OUT" | grep -c "FAILED" || true)
  PASS_COUNT=$(echo "$PYTEST_OUT" | grep -oP '[0-9]+ passed' | grep -oP '[0-9]+' || echo "0")
  if [[ "$FAIL_COUNT" -gt 0 ]]; then
    fail "pytest: $FAIL_COUNT test(s) FAILED"
  else
    success "pytest: $PASS_COUNT test(s) passed"
  fi
else
  warning "pytest not installed or tests/ not found — skipping. (pip install pytest pytest-cov)"
fi

# ── 4. Documentation (pydocstyle) ─────────────────────────────────────────────
header "STEP 4 / 4 — Documentation (pydocstyle)"
if command -v pydocstyle &>/dev/null && [[ -n "$PY_FILES" ]]; then
  DOC_OUT=$(pydocstyle $PY_FILES 2>&1 || true)
  MISSING=$(echo "$DOC_OUT" | grep -c "Missing docstring" || true)
  echo "$DOC_OUT"
  if [[ "$MISSING" -gt 0 ]]; then
    warning "pydocstyle: $MISSING function(s) missing docstrings"
  else
    success "pydocstyle: all public functions documented"
  fi
else
  warning "pydocstyle not installed or no Python files found — skipping. (pip install pydocstyle)"
fi

# ── Append run record to REVIEW_SUMMARY.md ───────────────────────────────────
header "Updating REVIEW_SUMMARY.md"
{
  echo ""
  echo "---"
  echo ""
  echo "## Automated Run — $TIMESTAMP"
  echo ""
  echo "| Step | Tool | Result |"
  echo "|---|---|---|"
  echo "| Security | bandit | see output above |"
  echo "| Code Quality | pylint | score: ${PYLINT_SCORE:-n/a} |"
  echo "| Test Coverage | pytest --cov | ${PASS_COUNT:-0} tests passed |"
  echo "| Documentation | pydocstyle | ${MISSING:-n/a} missing docstrings |"
  echo ""
  echo "> Run triggered by: \`$(git -C "$REPO_ROOT" log -1 --pretty=format:"%h %s" 2>/dev/null || echo "unknown")\`"
} >> "$SUMMARY_FILE"
success "Appended run record to REVIEW_SUMMARY.md"

# ── Final status ──────────────────────────────────────────────────────────────
header "Review Complete"
if [[ "$EXIT_CODE" -eq 0 ]]; then
  echo "  ✅  All checks passed — no blocking issues found."
else
  echo "  ❌  One or more checks found blocking issues. Review the output above."
fi
echo ""
exit "$EXIT_CODE"
