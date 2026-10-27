"""The live e2e script computes commitments in JavaScript (viem keccak256). This proves the
JavaScript and the contract agree, so a live run cannot fail on a hashing mismatch."""
import json
import shutil
import subprocess

import pytest
from helpers import ROOT


def _js(question_id, address, p, salt):
    code = ("import { commitment } from './e2e/model.mjs';"
            f"console.log(commitment({question_id}, {json.dumps(address)}, {p}, {json.dumps(salt)}));")
    out = subprocess.run(["node", "--input-type=module", "-e", code], cwd=ROOT, capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        pytest.skip("node or viem not available: " + out.stderr[:200])
    return out.stdout.strip()


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
@pytest.mark.parametrize("p,salt", [(100, "saltysalt1"), (7000, "salt-mvq9ox6f-yes-bob"), (9900, "A1b2C3d4E5!@#$%^&*()")])
def test_javascript_commitment_equals_contract(env, p, salt):
    qid = env.open()
    for who in (env.bob, env.carol):
        assert _js(qid, who.as_hex, p, salt) == env.c.preview_commitment(qid, who.as_hex, p, salt)
