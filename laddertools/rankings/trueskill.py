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

from .abc import RankingBase


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


class RankingTrueskill(RankingBase):

    def __init__(self):
        self._env = trueskill.TrueSkill(draw_probability=0)

    def record_result(self, winner_rating, loser_rating):
        r0, r1 = self._env.rate_1vs1(winner_rating.internal, loser_rating.internal)
        r0 = _RatingTrueskill(self._env, r0)
        r1 = _RatingTrueskill(self._env, r1)
        return r0, r1

    @classmethod
    def get_default_rating(cls):
        return _RatingTrueskill(cls()._env)
