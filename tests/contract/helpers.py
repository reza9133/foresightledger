"""Shared helpers for the ForesightLedger direct-mode contract tests."""
import datetime as dt
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = os.environ.get("FL_CONTRACT") or str(ROOT / "contracts" / "foresight_ledger.py")
VECTORS = json.loads((ROOT / "tests" / "fixtures" / "url_vectors.json").read_text())["vectors"]

URL = "https://example.com/status"
TITLE = "Will the Orion probe reach orbit?"
CRITERIA = "Resolves YES if the status page reports that the Orion probe entered orbit."

PAGE_YES = "Mission status. The Orion probe has successfully entered orbit around the target planet."
PAGE_NO = "Mission status. The Orion mission was cancelled and the probe will never launch."
PAGE_OPEN = "Mission status. The Orion probe is still in transit and arrival is expected next quarter."
PAGE_OTHER = "Welcome to our cooking blog. Today: sourdough."

QUOTE_YES = "Orion probe has successfully entered orbit"
QUOTE_NO = "mission was cancelled and the probe will never launch"

HOUR = 3600
DAY = 86400


def iso(ts: int) -> str:
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).isoformat().replace("+00:00", "Z")


def llm_json(verdict="YES", summary="A one sentence summary.", citation=""):
    return json.dumps({"verdict": verdict, "summary": summary, "citation": citation})


class Env:
    """A deployed ledger plus the VM and a few conveniences."""

    def __init__(self, vm, contract, accounts):
        self.vm = vm
        self.c = contract
        self.alice, self.bob, self.carol = accounts

    # ---- time -------------------------------------------------------
    def now(self) -> int:
        raw = self.vm._datetime
        return int(dt.datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp())

    def warp_to(self, ts: int):
        # gltest's warp() updates the VM clock but does not refresh the cached
        # gl.message_raw["datetime"] the contract reads, so do it here too.
        import sys

        self.vm.warp(iso(ts))
        gl = sys.modules.get("genlayer.gl")
        if gl is not None and getattr(gl, "message_raw", None) is not None:
            gl.message_raw["datetime"] = iso(ts)

    def advance(self, seconds: int):
        self.warp_to(self.now() + seconds)

    # ---- mocks ------------------------------------------------------
    def page(self, body: str, pattern=r"example\.com.*"):
        self.vm._web_mocks.clear()
        self.vm.mock_web(pattern, {"status": 200, "body": body})

    def llm(self, verdict="YES", summary="A one sentence summary.", citation=""):
        self.vm._llm_mocks.clear()
        self.vm.mock_llm(r".*", llm_json(verdict, summary, citation))

    def llm_raw(self, text: str):
        self.vm._llm_mocks.clear()
        self.vm.mock_llm(r".*", text)

    def no_web(self):
        self.vm._web_mocks.clear()

    # ---- actors -----------------------------------------------------
    def extra(self, n: int):
        """A deterministic extra account (alice/bob/carol are the first three)."""
        from genlayer import Address

        return Address(bytes([0xA0 + n]) * 20)

    # ---- actions ----------------------------------------------------
    def as_(self, who):
        self.vm.sender = who

    def open(self, title=TITLE, criteria=CRITERIA, url=URL, close_in=HOUR, window=DAY,
             sender=None, body=PAGE_OPEN):
        if sender is not None:
            self.vm.sender = sender
        if body is not None:
            self.page(body)
        return int(self.c.open_question(title, criteria, url, self.now() + close_in, window))

    def commit_hash(self, qid, who, p, salt):
        return self.c.preview_commitment(qid, who.as_hex, p, salt)

    def commit(self, qid, who, p, salt="saltysalt1"):
        self.vm.sender = who
        return int(self.c.commit_forecast(qid, self.commit_hash(qid, who, p, salt)))

    def reveal(self, qid, who, p, salt="saltysalt1"):
        self.vm.sender = who
        self.c.reveal_forecast(qid, p, salt)

    def to_reveal(self, qid=1):
        q = self.c.get_question(qid)
        self.warp_to(int(q.close_at))

    def to_resolve(self, qid=1):
        q = self.c.get_question(qid)
        self.warp_to(int(q.reveal_until))

    def resolve(self, qid=1, verdict="YES", citation="", body=None, sender=None, summary="Summary."):
        if sender is not None:
            self.vm.sender = sender
        if body is not None:
            self.page(body)
        self.llm(verdict, summary, citation)
        return int(self.c.resolve_question(qid))

    def cooldown(self):
        self.advance(301)

    def stats(self):
        return dict(self.c.get_stats())

    def revert(self, text=None):
        return self.vm.expect_revert(text)


def user_error(message: str):
    """A GenVM UserError; the SDK only becomes importable once a contract was loaded."""
    from genlayer import gl

    return gl.vm.UserError(message)
