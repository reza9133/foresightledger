"""Mutation check: break the contract in a known way and require the test suite to notice.

Usage: python scripts/mutation_check.py [pytest-executable]
Every mutation must be KILLED (at least one test fails). A SURVIVOR means a rule
of the contract is not protected by the tests.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "contracts" / "foresight_ledger.py").read_text()
PYTEST = sys.argv[1] if len(sys.argv) > 1 else "pytest"

MUTATIONS = [
    ("commit window off by one", "if now >= int(question.close_at):\n            raise gl.vm.UserError(\"[EXPECTED] the commit window is closed\")",
     "if now > int(question.close_at):\n            raise gl.vm.UserError(\"[EXPECTED] the commit window is closed\")"),
    ("creator may forecast", "if sender == question.creator:", "if False:"),
    ("duplicate commit allowed", "if self.forecast_lookup.get(key) is not None:", "if False:"),
    ("forecast cap removed", "if int(question.forecast_count) >= MAX_FORECASTS_PER_QUESTION:", "if False:"),
    ("sender dropped from preimage", 'f"foresight-v1|{question_id}|{forecaster_hex.lower()}|{probability_bps}|{salt}"',
     'f"foresight-v1|{question_id}|{probability_bps}|{salt}"'),
    ("reveal skips hash check", "if _commitment(qid, sender.as_hex, probability, salt) != forecast.commitment:", "if False:"),
    ("reveal window end inclusive", "if now >= int(question.reveal_until):\n            raise gl.vm.UserError(\"[EXPECTED] the reveal window is closed\")",
     "if now > int(question.reveal_until):\n            raise gl.vm.UserError(\"[EXPECTED] the reveal window is closed\")"),
    ("probability range widened", "MAX_PROBABILITY_BPS = 9900", "MAX_PROBABILITY_BPS = 10000"),
    ("resolve before reveal window ends", "if now < int(question.reveal_until):\n            raise gl.vm.UserError(\"[EXPECTED] resolution opens", "if False:\n            raise gl.vm.UserError(\"[EXPECTED] resolution opens"),
    ("no cooldown", "if last and now - last < MIN_ATTEMPT_INTERVAL_SECONDS:", "if False:"),
    ("no quote still decisive", "if verdict in _DECISIVE_VERDICTS and not citation:", "if False:"),
    ("citation not grounded", 'if cleaned.lower() not in snapshot.lower():\n        return ""', "if False:\n        return \"\""),
    ("validator skips quote check", "if citation and _ground_citation(citation, mine_snapshot) != citation:", "if False:"),
    ("validator skips verdict match", 'return mine["verdict"] == verdict', "return True"),
    ("validator accepts model failure", 'return leader_data.get("reason") == "fetch" and mine_snapshot is None', "return True"),
    ("brier formula wrong", "return (delta * delta) // BPS_SCALE", "return abs(delta) // 100"),
    ("forfeit not penalised", "forecast.brier_bps = u256(WORST_BRIER_BPS)\n                record.forfeited", "forecast.brier_bps = u256(0)\n                record.forfeited"),
    ("crowd includes nothing", "crowd_bps = revealed_sum // revealed_n", "crowd_bps = 5000"),
    ("beat crowd non-strict", "beat = brier < crowd_brier", "beat = brier <= crowd_brier"),
    ("hit uses >= 5000", "hit = (probability > 5000 and yes)", "hit = (probability >= 5000 and yes)"),
    ("calibration bucket wrong", "bucket = min(probability // 1000, CALIBRATION_BUCKETS - 1)", "bucket = min(probability // 1100, CALIBRATION_BUCKETS - 1)"),
    ("void without grace", "if now < int(question.reveal_until) + VOID_GRACE_SECONDS:", "if False:"),
    ("void leaves forecasts live", "forecast.status = F_VOID", "pass"),
    ("settled question can be voided", "if question.status != Q_OPEN:\n            raise gl.vm.UserError(\"[EXPECTED] question is already settled\")\n        if now < int(question.reveal_until) + VOID", "if False:\n            raise gl.vm.UserError(\"[EXPECTED] question is already settled\")\n        if now < int(question.reveal_until) + VOID"),
    ("duplicate question allowed", "if existing is not None:", "if False:"),
    ("creator cap removed", "if mine is not None and len(mine) >= MAX_QUESTIONS_PER_CREATOR:", "if False:"),
    ("reachability skipped", "if not self._check_reachable(source_url):", "if False:"),
    ("ssrf: private 10/8 allowed", "(_v4(10, 0, 0, 0), 8),", ""),
    ("ssrf: port check removed", 'if sep and port not in ("", "443"):', "if False:"),
    ("delimiters not neutralised", 'return text.replace("<<<", "\\u2039\\u2039\\u2039").replace(">>>", "\\u203a\\u203a\\u203a")', "return text"),
    ("model failure recorded", 'if not result.get("ok") and result.get("reason") != "fetch":', "if False:"),
    ("skill sign asymmetric", "skill = (diff // scored if diff >= 0 else -((-diff) // scored)) if scored else 0", "skill = diff // scored if scored else 0"),
]


def main() -> int:
    survivors = []
    for name, old, new in MUTATIONS:
        if SRC.count(old) != 1:
            print(f"SKIP  {name}: pattern matched {SRC.count(old)} times")
            survivors.append(name + " (bad pattern)")
            continue
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "foresight_ledger.py"
            path.write_text(SRC.replace(old, new))
            env = dict(os.environ, FL_CONTRACT=str(path))
            proc = subprocess.run([PYTEST, "-q", "-x", "-p", "no:cacheprovider"], cwd=ROOT, env=env,
                                  capture_output=True, text=True)
        killed = proc.returncode != 0
        print(("KILLED   " if killed else "SURVIVED ") + name, flush=True)
        if not killed:
            survivors.append(name)
    print(f"\n{len(MUTATIONS) - len(survivors)}/{len(MUTATIONS)} mutations killed")
    if survivors:
        print("survivors:", ", ".join(survivors))
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main())
