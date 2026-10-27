import pytest
from helpers import *


def test_version_and_limits(env):
    assert env.c.get_version() == "1.0.0"
    lim = dict(env.c.get_limits())
    assert lim["max_forecasts_per_question"] == 40 and lim["void_grace_seconds"] == 14 * DAY
    assert lim["min_probability_bps"] == 100 and lim["max_probability_bps"] == 9900


def test_fresh_contract(env):
    s = env.stats()
    assert s["total_questions"] == 0 and s["open"] == 0 and s["forecasters"] == 0 and s["report_count"] == 0
    assert list(env.c.list_questions(0, 10)) == [] and list(env.c.list_forecasters(0, 10)) == []
    assert all(b["total"] == 0 for b in dict(env.c.get_calibration())["buckets"])


@pytest.mark.parametrize("bad", ["", "0x12", "bob", "0x" + "g" * 40, "0x" + "a" * 41, "a" * 42])
def test_bad_addresses_are_rejected_cleanly(env, bad):
    for call in (lambda: env.c.get_forecaster(bad), lambda: env.c.get_forecaster_summary(bad),
                 lambda: env.c.list_creator_questions(bad), lambda: env.c.list_forecaster_forecasts(bad, 0, 5),
                 lambda: env.c.preview_commitment(1, bad, 5000, "saltysalt1")):
        with env.revert("address must be"):
            call()


def test_not_found(env):
    qid = env.open()
    with env.revert("question not found"):
        env.c.get_question(7)
    with env.revert("forecast not found"):
        env.c.get_forecast(1)
    with env.revert("report not found"):
        env.c.get_report(1)
    with env.revert("forecaster not found"):
        env.c.get_forecaster(env.bob.as_hex)
    with env.revert("no forecast from this address"):
        env.c.get_forecast_for(qid, env.bob.as_hex)
    with env.revert("question not found"):
        env.c.list_question_forecasts(9)
    with env.revert("question not found"):
        env.c.list_question_reports(9, 0, 5)
    assert list(env.c.list_creator_questions(env.bob.as_hex)) == []
    assert list(env.c.list_forecaster_forecasts(env.bob.as_hex, 0, 5)) == []


def test_listing_per_forecaster_is_paginated(env):
    for i in range(3):
        qid = env.open(title=f"Listing question {i} here", url=f"https://example.com/l{i}", sender=env.alice)
        env.commit(qid, env.bob, 5000)
    ids = [int(f.id) for f in env.c.list_forecaster_forecasts(env.bob.as_hex, 0, 10)]
    assert ids == [1, 2, 3]
    assert [int(f.id) for f in env.c.list_forecaster_forecasts(env.bob.as_hex, 1, 1)] == [2]
    assert [int(f.id) for f in env.c.list_question_forecasts(2)] == [2]


def test_address_case_does_not_matter(env):
    qid = env.open()
    env.commit(qid, env.bob, 5000)
    f = env.c.get_forecast_for(qid, env.bob.as_hex.lower())
    assert f.forecaster == env.bob
    assert env.c.preview_commitment(qid, env.bob.as_hex.lower(), 5000, "saltysalt1") == f.commitment
