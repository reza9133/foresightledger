import pytest
from helpers import *


def _q(env):
    return env.open()


def test_commit_and_reveal_happy_path(env):
    qid = _q(env)
    fid = env.commit(qid, env.bob, 7000)
    f = env.c.get_forecast(fid)
    assert f.status == "SEALED" and f.probability_bps == 0 and f.forecaster == env.bob
    assert f.commitment == env.commit_hash(qid, env.bob, 7000, "saltysalt1")
    assert env.c.get_question(qid).forecast_count == 1
    env.to_reveal(qid)
    env.reveal(qid, env.bob, 7000)
    f = env.c.get_forecast(fid)
    assert f.status == "REVEALED" and f.probability_bps == 7000 and f.revealed_at == env.now()
    q = env.c.get_question(qid)
    assert q.revealed_count == 1
    rec = env.c.get_forecaster(env.bob.as_hex)
    assert (rec.committed, rec.revealed) == (1, 1)
    assert env.stats()["reveals"] == 1 and env.stats()["total_forecasts"] == 1


def test_commitment_matches_independent_preimage(env):
    from genlayer import Keccak256
    qid = _q(env)
    h = Keccak256()
    h.update(f"foresight-v1|{qid}|{env.bob.as_hex.lower()}|6500|abcdefgh".encode())
    assert env.commit_hash(qid, env.bob, 6500, "abcdefgh") == h.hexdigest()


def test_commit_window_boundary(env):
    qid = _q(env)
    env.warp_to(int(env.c.get_question(qid).close_at) - 1)
    env.commit(qid, env.bob, 5000)
    env.to_reveal(qid)
    with env.revert("commit window is closed"):
        env.commit(qid, env.carol, 5000)


def test_commit_validation(env):
    qid = _q(env)
    env.as_(env.bob)
    for bad in ["", "abc", "z" * 64, "0" * 63, "0" * 65, "0x" + "0" * 62]:
        with env.revert("32-byte hex"):
            env.c.commit_forecast(qid, bad)
    with env.revert("question not found"):
        env.c.commit_forecast(99, "0" * 64)
    # 0x prefix and upper case are normalised
    h = env.commit_hash(qid, env.bob, 5000, "saltysalt1")
    env.c.commit_forecast(qid, "0X" + h.upper()[0:64])
    assert env.c.get_forecast_for(qid, env.bob.as_hex).commitment == h


def test_creator_cannot_forecast_own_question(env):
    qid = _q(env)
    with env.revert("creator may not forecast"):
        env.commit(qid, env.alice, 5000)


def test_one_commit_per_address_per_question(env):
    qid = _q(env)
    env.commit(qid, env.bob, 5000)
    with env.revert("already committed"):
        env.commit(qid, env.bob, 6000, "othersalt1")
    q2 = env.open(title="A second question here", url="https://example.com/two", sender=env.alice)
    env.commit(q2, env.bob, 6000)
    assert env.stats()["total_forecasts"] == 2


def test_forecast_cap_per_question(env):
    qid = _q(env)
    for i in range(40):
        env.commit(qid, env.extra(i), 5000)
    with env.revert("forecast limit"):
        env.commit(qid, env.bob, 5000)
    assert env.c.get_question(qid).forecast_count == 40


def test_copied_commitment_cannot_be_revealed_by_copier(env):
    qid = _q(env)
    env.commit(qid, env.bob, 9000)
    stolen = env.commit_hash(qid, env.bob, 9000, "saltysalt1")
    env.as_(env.carol)
    env.c.commit_forecast(qid, stolen)
    env.to_reveal(qid)
    with env.revert("do not match"):
        env.reveal(qid, env.carol, 9000)
    env.reveal(qid, env.bob, 9000)


def test_reveal_window_rules(env):
    qid = _q(env)
    env.commit(qid, env.bob, 7000)
    with env.revert("not opened yet"):
        env.reveal(qid, env.bob, 7000)
    env.to_reveal(qid)
    env.reveal(qid, env.bob, 7000)
    q2 = env.open(title="A second question here", url="https://example.com/two", sender=env.alice)
    env.commit(q2, env.carol, 7000)
    env.to_resolve(q2)
    with env.revert("reveal window is closed"):
        env.reveal(q2, env.carol, 7000)


def test_reveal_last_second_is_allowed(env):
    qid = _q(env)
    env.commit(qid, env.bob, 7000)
    env.warp_to(int(env.c.get_question(qid).reveal_until) - 1)
    env.reveal(qid, env.bob, 7000)


@pytest.mark.parametrize("p,salt,msg", [
    (7001, "saltysalt1", "do not match"),
    (7000, "wrongsalt1", "do not match"),
    (99, "saltysalt1", "between 100 and 9900"),
    (9901, "saltysalt1", "between 100 and 9900"),
    (0, "saltysalt1", "between 100 and 9900"),
    (10000, "saltysalt1", "between 100 and 9900"),
    (7000, "short", "salt must be"),
    (7000, "x" * 65, "salt must be"),
    (7000, "has|pipe1234", "salt must be"),
    (7000, "has space123", "printable ASCII"),
    (7000, "tab\tinside1", "printable ASCII"),
])
def test_reveal_rejections(env, p, salt, msg):
    qid = _q(env)
    env.commit(qid, env.bob, 7000)
    env.to_reveal(qid)
    with env.revert(msg):
        env.reveal(qid, env.bob, p, salt)
    assert env.c.get_forecast_for(qid, env.bob.as_hex).status == "SEALED"
    assert env.stats()["reveals"] == 0


def test_reveal_without_commit_or_twice(env):
    qid = _q(env)
    env.commit(qid, env.bob, 7000)
    env.to_reveal(qid)
    with env.revert("no committed forecast"):
        env.reveal(qid, env.carol, 7000)
    env.reveal(qid, env.bob, 7000)
    with env.revert("already revealed"):
        env.reveal(qid, env.bob, 7000)
    assert env.c.get_question(qid).revealed_count == 1


@pytest.mark.parametrize("p", [100, 9900, 5000])
def test_probability_extremes_accepted(env, p):
    qid = _q(env)
    env.commit(qid, env.bob, p)
    env.to_reveal(qid)
    env.reveal(qid, env.bob, p)
    assert env.c.get_forecast_for(qid, env.bob.as_hex).probability_bps == p


def test_commit_unknown_or_settled_question(env):
    qid = _q(env)
    env.to_resolve(qid)
    env.resolve(qid, "YES", QUOTE_YES, body=PAGE_YES)
    with env.revert("no longer open"):
        env.commit(qid, env.bob, 5000)
    with env.revert("no longer open"):
        env.reveal(qid, env.bob, 5000)
