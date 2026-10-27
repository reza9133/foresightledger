import random
import pytest
from helpers import *


def brier(p, outcome):
    return (p - outcome) ** 2 // 10000


def play(env, probs, outcome_yes, unrevealed=(), title=None, url=None):
    """probs: {account_index: p}; unrevealed: account indices that commit but never reveal."""
    qid = env.open(title=title or TITLE, url=url or URL, sender=env.alice)
    for i, p in probs.items():
        env.commit(qid, env.extra(i), p)
    for i in unrevealed:
        env.commit(qid, env.extra(i), 5000)
    env.to_reveal(qid)
    for i, p in probs.items():
        env.reveal(qid, env.extra(i), p)
    env.to_resolve(qid)
    if outcome_yes:
        env.resolve(qid, "YES", QUOTE_YES, body=PAGE_YES, sender=env.alice)
    else:
        env.resolve(qid, "NO", QUOTE_NO, body=PAGE_NO, sender=env.alice)
    return qid


def test_exact_scores_yes(env):
    qid = play(env, {1: 8000, 2: 3000}, True)
    q = env.c.get_question(qid)
    assert q.crowd_bps == 5500 and q.crowd_brier_bps == 2025
    a = env.c.get_forecast_for(qid, env.extra(1).as_hex)
    b = env.c.get_forecast_for(qid, env.extra(2).as_hex)
    assert (a.status, a.brier_bps, a.hit, a.beat_crowd, a.crowd_brier_bps) == ("SCORED", 400, True, True, 2025)
    assert (b.status, b.brier_bps, b.hit, b.beat_crowd) == ("SCORED", 4900, False, False)


def test_exact_scores_no(env):
    qid = play(env, {1: 8000, 2: 3000}, False)
    a = env.c.get_forecast_for(qid, env.extra(1).as_hex)
    b = env.c.get_forecast_for(qid, env.extra(2).as_hex)
    assert (a.brier_bps, a.hit, a.beat_crowd) == (6400, False, False)
    assert (b.brier_bps, b.hit, b.beat_crowd) == (900, True, True)


def test_single_forecaster_ties_the_crowd_and_does_not_beat_it(env):
    qid = play(env, {1: 9000}, True)
    f = env.c.get_forecast_for(qid, env.extra(1).as_hex)
    assert f.brier_bps == 100 and f.crowd_brier_bps == 100 and not f.beat_crowd


def test_fifty_percent_is_never_a_hit(env):
    qid = play(env, {1: 5000}, True)
    f = env.c.get_forecast_for(qid, env.extra(1).as_hex)
    assert f.brier_bps == 2500 and not f.hit


def test_forfeit_is_worst_score_and_excluded_from_crowd(env):
    qid = play(env, {1: 9000}, True, unrevealed=(2,))
    q = env.c.get_question(qid)
    assert q.crowd_bps == 9000 and q.forfeited_count == 1
    f = env.c.get_forecast_for(qid, env.extra(2).as_hex)
    assert f.status == "FORFEITED" and f.brier_bps == 10000 and not f.hit
    s = dict(env.c.get_forecaster_summary(env.extra(2).as_hex))
    assert s["forfeited"] == 1 and s["scored"] == 0 and s["avg_brier_bps"] == 10000 and s["has_data"]
    assert s["skill_vs_crowd_bps"] == 0 and s["hit_rate_bps"] == 0
    assert env.stats()["forfeits"] == 1


def test_hiding_cannot_beat_showing_up(env):
    # A forecaster who is badly wrong is still better off revealing than forfeiting.
    play(env, {1: 100}, True, unrevealed=(2,))
    shown = dict(env.c.get_forecaster_summary(env.extra(1).as_hex))["avg_brier_bps"]
    hidden = dict(env.c.get_forecaster_summary(env.extra(2).as_hex))["avg_brier_bps"]
    assert shown == brier(100, 10000) == 9801 and hidden == 10000 and shown < hidden


def test_all_forfeit_has_no_crowd(env):
    qid = play(env, {}, True, unrevealed=(1, 2))
    q = env.c.get_question(qid)
    assert q.crowd_bps == 0 and q.forfeited_count == 2 and q.status == "RESOLVED_YES"


def test_forecaster_track_record_accumulates_across_questions(env):
    play(env, {1: 8000, 2: 3000}, True, title="First scored question", url="https://example.com/1")
    play(env, {1: 6000, 2: 2000}, False, title="Second scored question", url="https://example.com/2")
    s1 = dict(env.c.get_forecaster_summary(env.extra(1).as_hex))
    s2 = dict(env.c.get_forecaster_summary(env.extra(2).as_hex))
    # extra1: q1 400 (crowd 2025), q2 3600 (crowd (4000)^2/1e4=1600)
    assert s1["scored"] == 2 and s1["avg_brier_bps"] == (400 + 3600) // 2
    assert s1["skill_vs_crowd_bps"] == -187
    assert s1["beat_crowd"] == 1 and s1["hits"] == 1 and s1["hit_rate_bps"] == 5000
    assert s2["avg_brier_bps"] == (4900 + 400) // 2 and s2["beat_crowd"] == 1 and s2["hits"] == 1
    assert [r.forecaster for r in env.c.list_forecasters(0, 10)] == [env.extra(1), env.extra(2)]
    assert env.stats()["forecasters"] == 2


def test_calibration_buckets(env):
    play(env, {1: 100, 2: 9900, 3: 5000, 4: 7999, 5: 8000}, True)
    buckets = dict(env.c.get_calibration())["buckets"]
    assert len(buckets) == 10
    by = {b["low_bps"]: b for b in buckets}
    assert (by[0]["total"], by[0]["yes"]) == (1, 1)
    assert (by[9000]["total"], by[9000]["yes"], by[9000]["observed_yes_bps"]) == (1, 1, 10000)
    assert (by[5000]["total"], by[7000]["total"], by[8000]["total"]) == (1, 1, 1)
    play(env, {1: 7500}, False, title="A second calibration q", url="https://example.com/2")
    by = {b["low_bps"]: b for b in dict(env.c.get_calibration())["buckets"]}
    assert (by[7000]["total"], by[7000]["yes"], by[7000]["observed_yes_bps"]) == (2, 1, 5000)
    assert sum(b["total"] for b in by.values()) == 6


def test_unrevealed_forecasts_of_unsettled_question_are_untouched(env):
    qid = env.open()
    env.commit(qid, env.bob, 5000)
    env.to_resolve(qid)
    env.resolve(qid, "NOT_YET", "", body=PAGE_OPEN)
    f = env.c.get_forecast_for(qid, env.bob.as_hex)
    assert f.status == "SEALED" and f.brier_bps == 0
    assert env.stats()["forfeits"] == 0


def test_random_scoring_matches_reference_model(env):
    rng = random.Random(1234)
    model = {}  # account -> dict
    total_forfeits = 0
    for n in range(8):
        k = rng.randint(1, 10)
        accounts = rng.sample(range(1, 20), k)
        probs, hidden = {}, []
        for a in accounts:
            if rng.random() < 0.25:
                hidden.append(a)
            else:
                probs[a] = rng.randint(100, 9900)
        yes = rng.random() < 0.5
        qid = play(env, probs, yes, unrevealed=tuple(hidden), title=f"Random question number {n}",
                   url=f"https://example.com/r{n}")
        outcome = 10000 if yes else 0
        crowd = sum(probs.values()) // len(probs) if probs else 0
        cb = brier(crowd, outcome) if probs else 0
        assert env.c.get_question(qid).crowd_bps == crowd
        for a, p in probs.items():
            m = model.setdefault(a, dict(scored=0, forfeited=0, bsum=0, csum=0, beat=0, hits=0))
            b = brier(p, outcome)
            m["scored"] += 1; m["bsum"] += b; m["csum"] += cb
            m["beat"] += b < cb
            m["hits"] += (p > 5000 and yes) or (p < 5000 and not yes)
        for a in hidden:
            m = model.setdefault(a, dict(scored=0, forfeited=0, bsum=0, csum=0, beat=0, hits=0))
            m["forfeited"] += 1
            total_forfeits += 1
    for a, m in model.items():
        rec = env.c.get_forecaster(env.extra(a).as_hex)
        assert (rec.scored, rec.forfeited, rec.brier_sum, rec.crowd_brier_sum, rec.beat_crowd, rec.hits) == (
            m["scored"], m["forfeited"], m["bsum"], m["csum"], m["beat"], m["hits"])
    assert env.stats()["forfeits"] == total_forfeits
    cal = dict(env.c.get_calibration())["buckets"]
    assert sum(b["total"] for b in cal) == sum(m["scored"] for m in model.values())
