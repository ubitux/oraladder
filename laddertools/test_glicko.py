import pytest
from .rankings.glicko import RankingGlicko, _RatingGlicko

import numpy


def test_glicko():
    # Based on example from https://www.glicko.net/glicko/glicko2.pdf
    me = _RatingGlicko(1500, 200, .06)
    opponents = [
        _RatingGlicko(1400, 30, .06),
        _RatingGlicko(1550, 100, .06),
        _RatingGlicko(1700, 300, .06),
    ]
    outcomes = [1, 0, 0]  # I won, then lost two

    new_rating = RankingGlicko.compute_new_rating(
        me, opponents, outcomes, tau=0.5, eps=1e-6
    )

    numpy.testing.assert_almost_equal(1464.06, new_rating.r, decimal=2)
    numpy.testing.assert_almost_equal(151.52, new_rating.RD, decimal=2)
    numpy.testing.assert_almost_equal(0.05999, new_rating.std, decimal=5)


def test_glicko_empty_period_will_increase_RD():
    me = _RatingGlicko(1500, 345, std=1.0)
    opponents = outcomes = []
    new_rating = RankingGlicko.compute_new_rating(me, opponents, outcomes)
    assert new_rating.RD == 350
    assert new_rating.r == me.r  # should remain unchanged... Only increase RD
