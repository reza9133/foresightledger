#!/usr/bin/env bash
# Runs once when the Codespace is created.
set -euo pipefail
npm ci
python3 -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements-dev.txt
# The contract tests download the GenVM SDK on first use. Some GitHub release lookups answer 404;
# pre-seeding the known-good release makes the first run reliable.
mkdir -p "$HOME/.cache/gltest-direct"
if [ ! -f "$HOME/.cache/gltest-direct/genvm-universal-v0.2.16.tar.xz" ]; then
  curl -fsSL -o "$HOME/.cache/gltest-direct/genvm-universal-v0.2.16.tar.xz" \
    "https://github.com/genlayerlabs/genvm/releases/download/v0.2.16/genvm-universal.tar.xz" || echo "GenVM SDK pre-download skipped (pytest will try again)"
fi
cat <<'MSG'

ForesightLedger is ready.

  npm run test:all     offline model tests + contract tests (no network, no wallet)
  npm run mutation     mutation check: proves the contract tests catch real bugs
  npm run deploy       deploy contracts/foresight_ledger.py to Studionet, prints the address
  npm run e2e          live Studionet end-to-end run (about 30 minutes) + report in reports/
  npm run e2e:quick    live run that stops after the commit window (about 10 minutes)
  npm run e2e:publish  commit and push the newest report

Live runs read the fixtures from this repository on raw.githubusercontent.com, so
e2e/fixtures must be pushed to the branch you run from (or set E2E_FIXTURE_BASE).
MSG
