"""Consensus logic: what a validator accepts or rejects, given the leader's result.

Direct mode runs the leader once and captures the validator closure; run_validator
replays it against the *current* mocks, so swapping mocks simulates a validator that
sees a different world than the leader."""
from helpers import *


def _leader(env, verdict="YES", citation=QUOTE_YES, body=PAGE_YES):
    qid = env.open()
    env.to_resolve(qid)
    env.vm.clear_validators()
    env.page(body)
    env.llm(verdict, "Summary.", citation)
    env.c.resolve_question(qid)
    return env.vm._captured_validators[-1][0]


def test_honest_leader_is_accepted(env):
    leader = _leader(env)
    assert leader["ok"] and leader["verdict"] == "YES" and leader["citation"] == QUOTE_YES
    assert env.vm.run_validator() is True


def test_page_bytes_may_differ_when_quote_and_verdict_hold(env):
    _leader(env)
    env.page(PAGE_YES + " Footer: rotating ad 8123.")
    assert env.vm.run_validator() is True


def test_rejects_when_quote_missing_from_validator_page(env):
    _leader(env)
    env.page(PAGE_OPEN)
    assert env.vm.run_validator() is False


def test_rejects_when_validator_model_disagrees(env):
    _leader(env)
    env.llm("NO", "x", "")
    assert env.vm.run_validator() is False


def test_validator_accepts_different_summary_wording(env):
    _leader(env)
    env.llm("YES", "Completely different words.", "something else entirely")
    assert env.vm.run_validator() is True


def test_rejects_a_leader_that_invents_a_quote(env):
    leader = _leader(env)
    assert env.vm.run_validator(leader_result=dict(leader, citation="The probe landed on a Tuesday")) is False


def test_rejects_unknown_verdict_and_wrong_types(env):
    leader = _leader(env)
    for bad in [dict(leader, verdict="MAYBE"), dict(leader, verdict=None), dict(leader, citation=5),
                dict(leader, summary=None), dict(leader, ok="yes"), dict(leader, ok=0)]:
        assert env.vm.run_validator(leader_result=bad) is False


def test_rejects_malformed_leader_results(env):
    _leader(env)
    for bad in ["nope", 7, None, [], {}]:
        assert env.vm.run_validator(leader_result=bad) is False


def test_rejects_a_leader_that_crashed(env):
    _leader(env)
    assert env.vm.run_validator(leader_error=user_error("boom")) is False


def test_decisive_verdict_without_quote_passes_consensus_but_is_downgraded(env):
    leader = _leader(env, citation="")
    assert leader["citation"] == "" and env.vm.run_validator() is True
    assert env.c.get_report(1).verdict == "UNRESOLVABLE"


def test_leader_fetch_failure_is_accepted_only_if_validator_cannot_read_either(env):
    qid = env.open()
    env.to_resolve(qid)
    env.vm.clear_validators()
    env.no_web(); env.llm("YES")
    env.c.resolve_question(qid)
    assert env.vm._captured_validators[-1][0] == {"ok": False, "reason": "fetch"}
    assert env.vm.run_validator() is True
    env.page(PAGE_YES)
    assert env.vm.run_validator() is False


def test_leader_model_failure_is_never_rubber_stamped(env):
    qid = env.open()
    env.to_resolve(qid)
    env.vm.clear_validators()
    env.page(PAGE_YES); env.llm_raw("garbage")
    try:
        env.c.resolve_question(qid)
    except Exception:
        pass
    assert env.vm._captured_validators[-1][0] == {"ok": False, "reason": "model"}
    assert env.vm.run_validator() is False
    env.no_web()
    assert env.vm.run_validator() is False


def test_leader_cannot_claim_fetch_failure_when_it_was_a_model_failure(env):
    leader = _leader(env)
    env.no_web()
    assert env.vm.run_validator(leader_result={"ok": False, "reason": "model"}) is False
    assert env.vm.run_validator(leader_result={"ok": False}) is False
    assert env.vm.run_validator(leader_result={"ok": False, "reason": "fetch"}) is True


def test_validator_rejects_ok_leader_when_it_cannot_read_page(env):
    _leader(env)
    env.no_web()
    assert env.vm.run_validator() is False


def test_open_question_pair_agrees_only_on_readability(env):
    env.vm.clear_validators()
    env.open()
    assert env.vm._captured_validators[-1][0] == {"readable": True}
    assert env.vm.run_validator() is True
    env.no_web()
    assert env.vm.run_validator() is False
    for bad in [{"readable": False}, {}, "x", None, {"readable": 1}]:
        env.page(PAGE_OPEN)
        assert env.vm.run_validator(leader_result=bad) is False
    env.no_web()
    assert env.vm.run_validator(leader_result={"readable": False}) is True
