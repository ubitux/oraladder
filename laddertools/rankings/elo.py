#
# Copyright (C) 2020-2021
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

from .abc import RankingBase


class _RatingELO:

    def __init__(self, value):
        self.value = value

    @property
    def display_value(self):
        return round(self.value)


class RankingELO(RankingBase):

    _k = 32

    @classmethod
    def _expected_score(cls, r0, r1):
        return 1 / (1 + 10 ** ((r0.value - r1.value) / 400))

    @classmethod
    def _elo(cls, old, expected, result):
        return old.value + cls._k * (result - expected)

    def record_result(self, winner_rating, loser_rating):
        exp0 = self._expected_score(loser_rating, winner_rating)
        exp1 = self._expected_score(winner_rating, loser_rating)
        r0 = _RatingELO(self._elo(winner_rating, exp0, 1))
        r1 = _RatingELO(self._elo(loser_rating, exp1, 0))
        return r0, r1

    @classmethod
    def get_default_rating(cls):
        return _RatingELO(1000)
