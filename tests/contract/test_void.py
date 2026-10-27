from helpers import *

GRACE = 14 * DAY


def _setup(env):
    qid = env.open()
    env.commit(qid, env.bob, 7000)
    env.commit(qid, env.carol, 3000)
    env.to_reveal(qid)
    env.reveal(qid, env.bob, 7000)
    return qid


def test_void_after_grace(env):
    qid = _setup(env)
    env.warp_to(int(env.c.get_question(qid).reveal_until) + GRACE)
    env.as_(env.extra(5))
    env.c.void_question(qid)
    q = env.c.get_question(qid)
    assert q.status == "VOID" and q.resolved_at == env.now()
    for f in env.c.list_question_forecasts(qid):
        assert f.status == "VOID" and f.brier_bps == 0
    s = env.stats()
    assert (s["voided"], s["open"], s["forfeits"]) == (1, 0, 0)
    assert env.c.get_forecaster(env.carol.as_hex).forfeited == 0
    assert dict(env.c.get_forecaster_summary(env.bob.as_hex))["has_data"] is False
    assert sum(b["total"] for b in dict(env.c.get_calibration())["buckets"]) == 0


def test_void_too_early(env):
    qid = _setup(env)
    env.warp_to(int(env.c.get_question(qid).reveal_until) + GRACE - 1)
    with env.revert("grace period"):
        env.c.void_question(qid)
    env.advance(1)
    env.c.void_question(qid)


def test_voided_question_is_final(env):
    qid = _setup(env)
    env.warp_to(int(env.c.get_question(qid).reveal_until) + GRACE)
    env.c.void_question(qid)
    with env.revert("already settled"):
        env.c.void_question(qid)
    env.page(PAGE_YES); env.llm("YES", "s", QUOTE_YES)
    with env.revert("already settled"):
        env.c.resolve_question(qid)
    with env.revert("no longer open"):
        env.commit(qid, env.extra(3), 5000)


def test_settled_question_cannot_be_voided(env):
    qid = _setup(env)
    env.to_resolve(qid)
    env.resolve(qid, "YES", QUOTE_YES, body=PAGE_YES)
    env.warp_to(env.now() + GRACE * 2)
    with env.revert("already settled"):
        env.c.void_question(qid)


def test_resolution_still_possible_after_grace_until_someone_voids(env):
    qid = _setup(env)
    env.warp_to(int(env.c.get_question(qid).reveal_until) + GRACE * 3)
    env.resolve(qid, "YES", QUOTE_YES, body=PAGE_YES)
    assert env.c.get_question(qid).status == "RESOLVED_YES"


def test_void_unknown_question(env):
    with env.revert("question not found"):
        env.c.void_question(3)
