#!/usr/bin/env bash
# Commits and pushes the reports/ directory (run it after `npm run e2e`).
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -f reports/e2e-latest.md ]; then echo "no report found: run npm run e2e first" >&2; exit 1; fi
overall=$(grep -m1 -o 'Overall: [A-Z]*' reports/e2e-latest.md || echo "Overall: ?")
git add reports
if git diff --cached --quiet; then echo "nothing new to commit"; exit 0; fi
git commit -m "Add live Studionet e2e report (${overall})"
git push
echo "report pushed"
