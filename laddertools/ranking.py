#
# Copyright (C) 2020
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import trueskill
from abc import ABC, abstractmethod


class _RankingBase(ABC):

    def compute_ratings_from_series_of_games(self, games, player_lookup):
        player_ratings = {}
        game_ratings = []
        for g in games:
            p0 = player_lookup[g.player0]
            p1 = player_lookup[g.player1]
            r0 = player_ratings.get(p0, self.get_default_rating())
            r1 = player_ratings.get(p1, self.get_default_rating())

            r0_new, r1_new = self.record_result(r0, r1)
            player_ratings[p0] = r0_new
            player_ratings[p1] = r1_new

            item = (r0_new, r1_new)
            game_ratings.append(item)
        return game_ratings

    @classmethod
    @abstractmethod
    def get_default_rating(cls):
        """Returns a new rating for an unrated player."""

    @abstractmethod
    def record_result(self, winner_rating, loser_rating):
        """Returns a pair of new ratings, one for the winner and one for the loser."""


class _RatingTrueskill:

    def __init__(self, env, internal=None):
        self.internal = trueskill.Rating() if internal is None else internal
        self._env = env

    @property
    def value(self):
        return self._env.expose(self.internal)

    @property
    def display_value(self):
        # XXX: needs more accuracy?
        return round(self.value * 100)


class RankingTrueskill(_RankingBase):

    def __init__(self):
        self._env = trueskill.TrueSkill(draw_probability=0)

    def record_result(self, winner_rating, loser_rating):
        r0, r1 = trueskill.rate_1vs1(winner_rating.internal, loser_rating.internal)
        r0 = _RatingTrueskill(self._env, r0)
        r1 = _RatingTrueskill(self._env, r1)
        return r0, r1

    @classmethod
    def get_default_rating(cls):
        return _RatingTrueskill(cls()._env)


class _RatingELO:

    def __init__(self, value):
        self.value = value

    @property
    def display_value(self):
        return round(self.value)


class RankingELO(_RankingBase):

    _k = 32

    @classmethod
    def _expected_score(cls, r0, r1):
        return 1 / (1 + 10 ** ((r0.value - r1.value) / 400))

    @classmethod
    def _elo(cls, old, expected, result):
        return old.value + cls._k * (result - expected)

    def record_result(self, winner_rating, loser_rating):
        exp0 = self._expected_score(winner_rating, loser_rating)
        exp1 = self._expected_score(loser_rating, winner_rating)
        r0 = _RatingELO(self._elo(winner_rating, exp0, 1))
        r1 = _RatingELO(self._elo(loser_rating, exp1, 0))
        return r0, r1

    @classmethod
    def get_default_rating(cls):
        return _RatingELO(1000)


ranking_systems = dict(
    trueskill=RankingTrueskill,
    elo=RankingELO,
)
