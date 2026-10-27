# ForesightLedger

Sealed forecasts, resolved from public web evidence by GenLayer validators, scored on-chain with an integer Brier score.

ForesightLedger is a GenLayer Intelligent Contract for **Studionet**. Anyone can open a yes/no question with plain-language resolution criteria and a public evidence URL. Forecasters seal their probability with a hash, reveal it later, and after the evidence page settles the question every forecast is scored: accuracy, edge over the crowd, forfeits and calibration, all computed in plain Python inside the contract.

## Why it exists

Forecasting reputation is only meaningful if (1) nobody can copy or herd on someone else's number, (2) nobody can hide their bad calls, and (3) the outcome is decided by evidence rather than by the person who asked. The contract enforces each of these:

| Problem | Mechanism |
| --- | --- |
| Copying / herding | Commit-reveal. The commitment includes the sender address, so a copied hash is useless to the copier. |
| Hiding bad calls | A committed-but-unrevealed forecast is `FORFEITED` and scored with the worst Brier value (10000). |
| Creator decides the outcome | Validators read the evidence URL; a verdict needs a verbatim quote. The creator cannot forecast their own question. |
| Hallucinated verdicts | "No quote, no verdict": a YES/NO without a citation found in the page becomes `UNRESOLVABLE`. |
| Stuck questions | After `reveal_until + 14 days` anyone can `void_question`; nothing is scored and nobody is penalised. |

## Lifecycle

```
open_question          commit_forecast        reveal_forecast        resolve_question
     |  COMMIT window       |   REVEAL window      |   RESOLVE window      |
     +----------------------+----------------------+-----------------------+----> time
   created              close_at             reveal_until        reveal_until + 14d: void allowed
```

1. **Open** - `open_question(title, criteria, source_url, close_at, reveal_window_seconds)`. The evidence URL must be a public `https://` URL and must be readable by the validators.
2. **Commit** (`now < close_at`) - `commit_forecast(question_id, commitment)` where `commitment = keccak256("foresight-v1|<question_id>|<your address, lower case>|<probability_bps>|<salt>")`. Compute it locally; `preview_commitment` exists for convenience, but a salt sent to a node is no longer secret.
3. **Reveal** (`close_at <= now < reveal_until`) - `reveal_forecast(question_id, probability_bps, salt)`. The contract recomputes the hash.
4. **Resolve** (`now >= reveal_until`) - `resolve_question(question_id)`. YES or NO settles the question and scores everyone. NOT_YET or UNRESOLVABLE is recorded as an attempt (5 minute cooldown) and the question stays open.
5. **Void** (`now >= reveal_until + 14 days`) - `void_question(question_id)` if nothing settled it.

## Scoring

All values are integers in basis points.

- `probability_bps` is between 100 and 9900. The outcome is 10000 (YES) or 0 (NO).
- `brier_bps = (probability_bps - outcome)^2 // 10000`. 0 is perfect, 10000 is the worst.
- **Crowd** = floor of the mean of all *revealed* probabilities on the question. A forecast *beats the crowd* when its Brier value is strictly lower than the crowd's.
- **Hit** = probability above 5000 on a YES, or below 5000 on a NO. Exactly 5000 is never a hit.
- **Forfeit** = committed, never revealed: Brier 10000, excluded from the crowd.
- `get_forecaster_summary` returns the derived track record: `avg_brier_bps` (forfeits included), `skill_vs_crowd_bps` (positive means better than the crowd, truncated toward zero), `beat_crowd`, `hit_rate_bps`.
- `get_calibration` returns ten 10%-wide buckets with how many scored forecasts landed in each and how many resolved YES.

## How consensus works

`resolve_question` uses a custom leader/validator pair (`gl.vm.run_nondet_unsafe`):

- The **leader** fetches the evidence page, asks the model for a verdict and a verbatim quote, and returns `{verdict, summary, citation, evidence_hash, evidence_len}`.
- Each **validator** fetches the page itself and accepts only if
  1. the leader's citation is a verbatim substring of the validator's *own* snapshot (plain Python, no model), and
  2. the validator's own independent model verdict equals the leader's verdict.
- Page bytes are not required to match, so live pages with ads or timestamps still reach consensus. The stored `evidence_hash` is the leader's fingerprint of what it saw; it is evidence, not something validators vote on.
- A reported fetch failure is only accepted if the validator cannot read the page either. A model failure is never accepted; the transaction simply does not settle and can be retried without burning the cooldown.

`open_question` uses a smaller pair that only agrees on "is the evidence page readable".

## Security notes

- Page text and question text are placed between delimiters in the prompt; `<<<` and `>>>` are rejected in user text and neutralised in page text.
- Evidence URLs are restricted to public `https` (port 443): private, loopback, link-local, CGNAT and reserved IPv4 ranges, non-canonical IPv4 spellings, IPv6 literals, userinfo, backslashes, percent tricks in the authority and internal-only suffixes are refused. 101 URL vectors are covered by tests.
- Limits: 40 forecasts per question, 25 questions per creator, evidence capped at 8000 characters, list views capped at 50 rows.
- Known limitation: addresses are free, so a determined user can run several accounts. The creator-cannot-forecast rule and the per-creator cap raise the cost; they do not remove it.
- Known limitation: the question's criteria are written by its creator. Vague criteria give vague resolutions; the contract only guarantees that the verdict is grounded in the evidence page.

## Public interface

Write methods: `open_question`, `commit_forecast`, `reveal_forecast`, `resolve_question`, `void_question`.

Read methods: `get_version`, `get_limits`, `get_stats`, `get_question`, `list_questions`, `get_forecast`, `get_forecast_for`, `list_question_forecasts`, `list_forecaster_forecasts`, `list_creator_questions`, `get_report`, `list_question_reports`, `get_forecaster`, `get_forecaster_summary`, `list_forecasters`, `get_calibration`, `preview_commitment`.

Question statuses: `OPEN`, `RESOLVED_YES`, `RESOLVED_NO`, `VOID`. Forecast statuses: `SEALED`, `REVEALED`, `SCORED`, `FORFEITED`, `VOID`. Phases (commit / reveal / awaiting resolution) are derived from `close_at` and `reveal_until`.

## Tests

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q                      # 220+ direct-mode contract tests
node --test e2e/model.test.mjs # offline tests of the live script's scoring model
python scripts/mutation_check.py   # 32 deliberate bugs, every one must be caught
```

The tests cover creation, URL safety, commit/reveal rules, every resolution path, exact scoring (including a randomised comparison against an independent model), void, validator behaviour with forged or malformed leader results, prompt-injection attempts and read views.

> Note: if `pytest` fails while downloading the GenVM SDK with an HTTP 404, download `genvm-universal.tar.xz` from the `v0.2.16` release of `genlayerlabs/genvm` and place it at `~/.cache/gltest-direct/genvm-universal-v0.2.16.tar.xz`.

## Deploy to Studionet

```bash
npm install
npm run deploy        # optional: FL_PRIVATE_KEY=0x...
```

The script funds a throw-away account with `sim_fundAccount`, deploys `contracts/foresight_ledger.py`, waits for `FINALIZED` and prints the contract address and explorer links. The constructor takes no arguments.

Example flow (times are unix seconds):

1. `open_question("Will the Orion probe reach orbit?", "Resolves YES if the status page reports that the probe entered orbit.", "https://example.com/status", <now + 3600>, 86400)`
2. Each forecaster computes `keccak256("foresight-v1|1|<address>|7000|<salt>")` locally and calls `commit_forecast(1, hash)`.
3. After `close_at`, each calls `reveal_forecast(1, 7000, "<salt>")`.
4. After `reveal_until`, anyone calls `resolve_question(1)`.

## Live end-to-end run on Studionet (GitHub Codespaces)

`e2e/live-e2e.mjs` runs the whole product against the real network and writes a report.

```bash
# 1. push the fixtures once (the validators fetch them from raw.githubusercontent.com)
git add -A && git commit -m "ForesightLedger" && git push

# 2. open the repository in a Codespace (setup runs automatically), then:
npm run e2e            # full run, about 30 minutes
npm run e2e:publish    # commit + push reports/ (the report is also in reports/e2e-latest.md)
```

`npm run e2e:quick` stops after the commit window (about 10 minutes) and skips reveal, resolution and scoring.
`npm run e2e -- --strict` also fails the run when a model-dependent observation differs from the expectation.

What the run does:

1. Creates four funded accounts (alice creates questions; bob, carol and dave forecast) and deploys the contract, or reuses `FL_CONTRACT_ADDRESS`.
2. Opens four questions backed by four fixture pages: *operational* (expected YES), *cancelled* (expected NO), *testing* (expected to stay open) and *injection* (a page that tries to order the judge to answer YES).
3. Commits sealed forecasts, then proves 20+ rejections with real transactions (creator forecasting, duplicate commit, malformed hash, early or late reveal, wrong salt or probability, double reveal, private/metadata/http evidence URLs, prompt delimiters, short criteria, bad windows, duplicate question, early resolve, early void, resolve cooldown). A rejection counts only if the matching counter in `get_stats` did not move and, when the receipt exposes the contract's message, the message matches.
4. Waits for the real commit and reveal windows, reveals, and asks real validators to resolve each question.
5. Re-computes every Brier score, the crowd forecast, hits, "beat the crowd", forfeits, per-forecaster records and the calibration buckets from the raw on-chain forecasts and compares them with what the contract stored; recounts every statistic by brute force.
6. Waits for every transaction to reach `FINALIZED` and records it.

The report (`reports/e2e-<timestamp>.md` plus a `.json`, and `reports/e2e-latest.md`) contains the step table, the outcome of each question and a **transaction manifest** with one row per transaction: action, whether it succeeded or was rejected as intended, wait time, `ACCEPTED`/`FINALIZED` status and explorer link.

Step kinds: **HARD** steps assert deterministic behaviour and fail the run; **MODEL** steps record what real LLM validators, the page renderer or network finality did, and only fail the run with `--strict`.

Optional environment variables: `FL_CONTRACT_ADDRESS`, `FL_PRIVATE_KEY`, `E2E_FIXTURE_BASE`, `E2E_FIXTURE_REF`, `E2E_COMMIT_SECONDS` (default 720), `E2E_REVEAL_SECONDS` (default 480), `E2E_FINALIZE_MINUTES` (default 12), `E2E_REPORT_DIR`. The public RPC allows 30 requests per minute; `e2e/throttle.mjs` keeps the run under that limit.

## Project layout

```
contracts/foresight_ledger.py   the Intelligent Contract
tests/contract/                 direct-mode test suite
tests/fixtures/url_vectors.json URL safety vectors
scripts/mutation_check.py       mutation testing of the contract rules
e2e/                            deploy script, live end-to-end run, fixtures, offline model tests
.devcontainer/                  Codespace setup
reports/                        live run reports
```
