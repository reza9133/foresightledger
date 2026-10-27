import pytest
from helpers import *


def _ready(env, probs=((7000, "bob"), (3000, "carol"))):
    qid = env.open()
    people = {"bob": env.bob, "carol": env.carol}
    for p, who in probs:
        env.commit(qid, people[who], p)
    env.to_reveal(qid)
    for p, who in probs:
        env.reveal(qid, people[who], p)
    env.to_resolve(qid)
    return qid


def test_yes_resolution(env):
    qid = _ready(env)
    rid = env.resolve(qid, "YES", QUOTE_YES, body=PAGE_YES, sender=env.extra(1))
    r = env.c.get_report(rid)
    q = env.c.get_question(qid)
    assert r.verdict == "YES" and r.raw_verdict == "YES" and r.decisive and not r.unreachable
    assert r.citation == QUOTE_YES and r.requester == env.extra(1) and len(r.evidence_hash) == 64
    assert r.evidence_len == len(PAGE_YES)
    assert q.status == "RESOLVED_YES" and q.resolution_report_id == rid and q.resolved_at == env.now()
    assert q.attempt_count == 1 and q.crowd_bps == 5000
    s = env.stats()
    assert (s["resolved_yes"], s["open"], s["resolution_attempts"], s["report_count"]) == (1, 0, 1, 1)


def test_no_resolution(env):
    qid = _ready(env)
    env.resolve(qid, "NO", QUOTE_NO, body=PAGE_NO)
    assert env.c.get_question(qid).status == "RESOLVED_NO"
    assert env.stats()["resolved_no"] == 1


def test_resolution_opens_exactly_at_reveal_until(env):
    qid = env.open()
    env.warp_to(int(env.c.get_question(qid).reveal_until) - 1)
    env.llm("YES", "s", QUOTE_YES)
    env.page(PAGE_YES)
    with env.revert("after the reveal window"):
        env.c.resolve_question(qid)
    env.advance(1)
    env.c.resolve_question(qid)


@pytest.mark.parametrize("verdict", ["NOT_YET", "UNRESOLVABLE"])
def test_non_decisive_verdicts_keep_question_open(env, verdict):
    qid = _ready(env)
    rid = env.resolve(qid, verdict, "", body=PAGE_OPEN)
    r = env.c.get_report(rid)
    q = env.c.get_question(qid)
    assert r.verdict == verdict and not r.decisive and q.status == "OPEN"
    assert q.attempt_count == 1 and q.resolution_report_id == 0
    assert env.c.get_forecast_for(qid, env.bob.as_hex).status == "REVEALED"
    env.cooldown()
    env.resolve(qid, "YES", QUOTE_YES, body=PAGE_YES)
    assert env.c.get_question(qid).status == "RESOLVED_YES"
    assert env.c.get_question(qid).attempt_count == 2
    assert [int(x.id) for x in env.c.list_question_reports(qid, 0, 10)] == [1, 2]


@pytest.mark.parametrize("raw", ["YES", "NO"])
def test_no_quote_no_verdict(env, raw):
    qid = _ready(env)
    rid = env.resolve(qid, raw, "", body=PAGE_YES)
    r = env.c.get_report(rid)
    assert r.raw_verdict == raw and r.verdict == "UNRESOLVABLE" and not r.decisive
    assert env.c.get_question(qid).status == "OPEN"


def test_hallucinated_or_short_quote_is_discarded(env):
    qid = _ready(env)
    rid = env.resolve(qid, "YES", "The probe landed on Tuesday", body=PAGE_YES)
    assert env.c.get_report(rid).verdict == "UNRESOLVABLE"
    env.cooldown()
    rid = env.resolve(qid, "YES", "orbit", body=PAGE_YES)  # real substring, < 6 chars? 5 chars
    assert env.c.get_report(rid).verdict == "UNRESOLVABLE"
    assert env.c.get_question(qid).status == "OPEN"


def test_quote_match_is_case_and_whitespace_insensitive_but_stored_cleaned(env):
    qid = _ready(env)
    rid = env.resolve(qid, "YES", "  ORION   probe\nhas SUCCESSFULLY entered orbit ", body=PAGE_YES)
    assert env.c.get_report(rid).citation == "ORION probe has SUCCESSFULLY entered orbit"


def test_lowercase_verdict_is_accepted(env):
    qid = _ready(env)
    rid = env.resolve(qid, "yes", QUOTE_YES, body=PAGE_YES)
    assert env.c.get_report(rid).verdict == "YES"


def test_cooldown_between_attempts(env):
    qid = _ready(env)
    env.resolve(qid, "NOT_YET", "", body=PAGE_OPEN)
    with env.revert("cooldown"):
        env.c.resolve_question(qid)
    env.advance(299)
    with env.revert("cooldown"):
        env.c.resolve_question(qid)
    env.advance(1)
    env.c.resolve_question(qid)


def test_settled_question_cannot_be_resolved_again(env):
    qid = _ready(env)
    env.resolve(qid, "YES", QUOTE_YES, body=PAGE_YES)
    env.cooldown()
    with env.revert("already settled"):
        env.c.resolve_question(qid)
    assert env.stats()["report_count"] == 1


def test_unknown_question(env):
    with env.revert("question not found"):
        env.c.resolve_question(5)


def test_fetch_failure_is_a_recorded_attempt(env):
    qid = _ready(env)
    env.no_web()
    env.llm("YES")
    rid = int(env.c.resolve_question(qid))
    r = env.c.get_report(rid)
    q = env.c.get_question(qid)
    assert r.unreachable and r.verdict == "UNRESOLVABLE" and not r.decisive and r.evidence_hash == ""
    assert q.status == "OPEN" and q.attempt_count == 1


@pytest.mark.parametrize("raw", [
    "not json at all", '{"verdict":"MAYBE","summary":"x","citation":""}', '{"verdict":"YES","summary":"","citation":""}',
    "[]", '{"summary":"x"}',
])
def test_garbage_model_output_reverts_without_trace(env, raw):
    qid = _ready(env)
    env.page(PAGE_YES)
    env.llm_raw(raw)
    before = env.stats()
    with env.revert("no usable verdict"):
        env.c.resolve_question(qid)
    assert env.stats() == before
    q = env.c.get_question(qid)
    assert q.attempt_count == 0 and q.last_attempt_at == 0
    env.resolve(qid, "YES", QUOTE_YES, body=PAGE_YES)  # no cooldown was burned
    assert env.c.get_question(qid).status == "RESOLVED_YES"


def test_question_with_no_forecasts_resolves(env):
    qid = env.open()
    env.to_resolve(qid)
    env.resolve(qid, "NO", QUOTE_NO, body=PAGE_NO)
    q = env.c.get_question(qid)
    assert q.status == "RESOLVED_NO" and q.crowd_bps == 0 and q.crowd_brier_bps == 0
    assert env.stats()["forecasters"] == 0
