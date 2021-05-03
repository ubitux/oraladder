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

from math import sqrt, pi, exp, log, hypot
from itertools import count
from datetime import timedelta
from collections import deque, defaultdict

from .abc import RankingBase


class _RatingGlicko:

    _initial_rating = 1500

    # scaling factor used to go from / to glicko to glicko-2 scale.
    _k = 173.7178

    def __init__(self, r0, RD, std):
        self.r = r0
        self.std = std
        self.RD = RD

    def duplicate(self, r=None, RD=None, std=None):
        return _RatingGlicko(r0=r or self.r, RD=RD or self.RD, std=std or self.std)

    @property
    def display_value(self):
        return round(self.value)

    @property
    def value(self):
        return self.r

    @property
    def mu(self):
        return (self.r - self._initial_rating) / self._k

    @property
    def phi(self):
        return self.RD / self._k

    @classmethod
    def mu_to_rating(cls, mu):
        return cls._k * mu + cls._initial_rating

    @classmethod
    def phi_to_RD(cls, phi):
        return cls._k * phi

    def __repr__(self):
        return f"<_RatingGlicko r={self.r:.1f}, RD={self.RD:.1f}, std={self.std:.4f}>"


class RankingGlicko(RankingBase):

    @staticmethod
    def compute_new_rating(
        rating,
        rating_opponents,
        outcomes,
        return_intermediate_ratings=False,
        tau=0.8,
        eps=1e-6,
    ):
        """Compute new rating for `rating`, given a series of M, where opponent i has rating
        `rating_opponents[i]` and the outcome is `outcomes[i]`.

        Computation is based on [1].

        Args:
            rating: instance of _RatingGlicko
            rating_opponents: list of length M; instances of _RatingGlicko
            outcomes: list of integers; 1 if `rating` won, 0 if lost.

        Returns:
            A new `_RatingGlicko` instance; the updated rating.

        References:
            [1]: https://www.glicko.net/glicko/glicko2.pdf
        """

        def g(rating):
            return 1 / sqrt(1 + (3 * rating.phi ** 2) / (pi ** 2))

        def E(rating, other):
            return 1 / (1 + exp(-g(other) * (rating.mu - other.mu)))

        if len(rating_opponents) == 0:
            # Shortcut: player did not have any matches, so we only increase
            # the RD.
            RD = _RatingGlicko.phi_to_RD(hypot(rating.phi, rating.std))
            RD = min(RD, 350)
            r = _RatingGlicko(rating.r, RD, rating.std)
            return (r, []) if return_intermediate_ratings else r

        # See Reference [1] for the steps 1,...,8.
        # Step 1 is to set the rating and RD for each player at the onset of
        # the rating period.
        # Step 2 is to convert to the glicko-2 scale, and we make helper
        # methods in `_RatingGlicko` to do that.

        # step 3, 4 -- compute `v` and `delta`. We use a for-loop and add the terms in the sum.
        delta = v = 0.0
        for opp, s in zip(rating_opponents, outcomes):
            e = E(rating, opp)
            v += g(opp) ** 2 * e * (1 - e)
            delta += g(opp) * (s - e)
        v = 1 / v
        delta = v * delta

        # step 5 -- determine the new value of std
        a = log(rating.std ** 2)

        def f(x):
            # f(x) = n1/d1 - n2/d2
            n1 = exp(x) * (delta ** 2 - rating.phi ** 2 - v - exp(x))
            d1 = 2 * (rating.phi ** 2 + v + exp(x)) ** 2
            n2 = x - a
            d2 = tau ** 2
            return n1 / d1 - n2 / d2

        A = a
        if delta ** 2 > rating.phi ** 2 + v:
            B = log(delta ** 2 - rating.phi ** 2 - v)
        else:
            for k in count(1):
                if (a - k * tau) < 0:
                    break
            B = a - k * tau

        f_A, f_B = f(A), f(B)
        while abs(B - A) > eps:
            C = A + (A - B) * f_A / (f_B - f_A)
            f_C = f(C)
            if f_C * f_B < 0:
                A, f_A = B, f_B
            else:
                f_A = f_A / 2
            B, f_B = C, f_C
        new_std = exp(A / 2)

        # step 6, 7, 8 -- update ratings
        phi_star = sqrt(rating.phi ** 2 + rating.std ** 2)

        new_phi = 1 / (phi_star ** 2) + 1 / v
        new_phi = 1 / sqrt(new_phi)

        new_mu = rating.mu + new_phi ** 2 * delta / v

        new_r = _RatingGlicko.mu_to_rating(new_mu)
        new_RD = _RatingGlicko.phi_to_RD(new_phi)
        new_rating = _RatingGlicko(r0=new_r, RD=new_RD, std=new_std)

        if return_intermediate_ratings:
            intermediate = []
            R_ = rating.duplicate()
            for r, o in zip(rating_opponents, outcomes):
                R_ = RankingGlicko.rate_1vs1(R_, r, o, tau=tau, eps=eps)
                intermediate.append(R_)
            return new_rating, intermediate

        return new_rating

    @classmethod
    def rate_1vs1(self, player, opponent, outcome, **kw):
        return RankingGlicko.compute_new_rating(player, [opponent], [outcome], **kw)

    def record_result(self, winner_rating, loser_rating):
        r0 = self.rate_1vs1(winner_rating, loser_rating, 1)
        r1 = self.rate_1vs1(loser_rating, winner_rating, 0)
        return r0, r1

    @classmethod
    def get_default_rating(cls):
        # Use a lower RD than the upper limit of 350. We use a lower RD because
        # we want to prevent new players from getting very high ratings based
        # on a couple of games.
        # In addition, we use a higher std than the 'default' 0.06 because we
        # except a higher fluctuation in rating, at least initially.
        return _RatingGlicko(_RatingGlicko._initial_rating, std=0.1, RD=100)

    def compute_ratings_from_series_of_games(
        self,
        games,
        player_lookup,
        rating_period=timedelta(days=3),
    ):
        """Computes the per-game rating of each involved player in `games`.

        Returns:
            a list of same length as `games`, where each elemnet is a pair of
            `_RatingGlicko` instances.
        """

        # (datetime, _Player) -> _RatingGlicko
        # ... this is the 'official' ratings. They are provided every
        # `rating_period`, and is the basis for rating calculation. Because a
        # player expects to get a new rating for every game played, we need
        # also to keep a collection of ratings by game. See below.
        player_ratings_by_period = {}

        def _previous_period_rating_for(player, current_period):
            key = (player, current_period - rating_period)
            if key not in player_ratings_by_period:
                return RankingGlicko.get_default_rating()
            return player_ratings_by_period[key]

        # game -> (_RatingGlicko, _RatingGlicko)
        # ... for `game.player0` and `game.player1` respectively
        player_ratings_by_game = {}

        def _group_games_by_player(games, player_lookup):
            out = defaultdict(list)
            for g in games:
                out[player_lookup[g.player0]].append(g)
                out[player_lookup[g.player1]].append(g)
            return dict(out)

        def _partition_games_in_rating_periods(games, start_time, rating_period):
            out = defaultdict(list)
            t = start_time
            remaining = deque(sorted(games, key=lambda g: g.start_time))
            while remaining:
                while remaining and t > remaining[0].end_time:
                    out[t].append(remaining.popleft())
                t += rating_period
                out[t] = []  # ensure we register a key for this rating period, too.
            return dict(out)

        def _get_opponent(game, player):
            p0 = player_lookup[game.player0]
            p1 = player_lookup[game.player1]
            if p0 is player:
                return p1
            elif p1 is player:
                return p0
            raise ValueError("Expected `player` to be involved in the game.")

        def _get_outcome_for(game, player):
            """Return 1 if `player` won the game, otherwise 0."""
            if player_lookup[game.player0] is player:
                return 1
            elif player_lookup[game.player1] is player:
                return 0
            raise ValueError("Expected `player` to be involved in the game.")

        start_date = min(map(lambda g: g.end_time, games))
        start_date = start_date.replace(hour=0, minute=0, second=0)

        games_by_period = _partition_games_in_rating_periods(
            games, start_date, rating_period
        )
        current_registered_players = set()

        for period, G in games_by_period.items():
            # TODO: if no games in particular period, we should still increase the RD.
            # Currently, we assume there's at least one game per period.
            groups = _group_games_by_player(G, player_lookup)
            current_registered_players = current_registered_players.union(groups.keys())
            for player in current_registered_players:
                G_ = groups.get(player, [])
                outcomes = [_get_outcome_for(g, player) for g in G_]
                opponents = [_get_opponent(g, player) for g in G_]
                opponent_ratings = [
                    _previous_period_rating_for(o, period) for o in opponents
                ]
                current_rating = _previous_period_rating_for(player, period)
                period - rating_period
                new_rating, tmp = RankingGlicko.compute_new_rating(
                    current_rating,
                    opponent_ratings,
                    outcomes,
                    return_intermediate_ratings=True,
                )
                for g, r in zip(G_, tmp):
                    player_ratings_by_game.setdefault(g, [None, None])
                    if player_lookup[g.player0] is player:
                        assert player_ratings_by_game[g][0] is None
                        player_ratings_by_game[g][0] = r
                    elif player_lookup[g.player1] is player:
                        assert player_ratings_by_game[g][1] is None
                        player_ratings_by_game[g][1] = r
                    else:
                        raise ValueError

                # We update the actual `r` value of `new_rating` by using the
                # last intermediate rating. Strictly speaking this is not
                # valid, because glicko-2 computes the rating once every
                # `rating_period`. However, we want a new rating after every
                # game, so we simply use the last intermediate rating as the
                # 'official rating'. But we keep RD and volatility constant
                # (equal to the official rating) during calculation of the
                # intermediate ratings.
                if len(tmp):
                    new_rating.r = tmp[-1].r

                player_ratings_by_period[player, period] = new_rating

        # The order of ratings must match the order of games. That's why we
        # can't return `player_ratings_by_game.values()` directly, since
        # they are not processed in the same order as `games` appear.
        return [player_ratings_by_game[g] for g in games]
