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

from abc import ABC, abstractmethod


class RankingBase(ABC):

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
