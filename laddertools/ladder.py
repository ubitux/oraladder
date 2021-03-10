#!/usr/bin/env python
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

import os
import os.path as op
import hashlib
import logging
import argparse
import sqlite3
from filelock import FileLock, Timeout
from collections import UserDict

from .replay import GamePlayerInfo
from .ranking import ranking_systems
from .utils import get_results


class PlayerLookup(UserDict):
    """Connects a `GamePlayerInfo` (or its fingerprint) to a `_Player`.

    Several way to access a player:
        1) From a `GamePlayerInfo`: `lookup[result.player0]`
        2) From the unique id: `lookup[6003]`
        3) From the player name (since it's also unique): `lookup['morkel']`.
           Notice this only works for __getitem__ and not __setitem__. The name
           is also case-sensitive.
    """

    def __init__(self, accounts_db, ranking):
        super().__init__()
        self.accounts_db = accounts_db
        self.ranking = ranking
        self._names = {}

    def _insert_from_fingerprint(self, fingerprint):
        profile_id, name, avatar_url = self.accounts_db.get(fingerprint)
        self.data.setdefault(
            profile_id, _Player(self.ranking, profile_id, name, avatar_url)
        )
        self._names.setdefault(self.data[profile_id].name, self.data[profile_id])
        return self.data[profile_id]

    def __getitem__(self, obj):
        if isinstance(obj, GamePlayerInfo):
            return self._insert_from_fingerprint(obj.fingerprint)
        if isinstance(obj, str):  # we assume it's the name of the player, then.
            if obj not in self._names:
                raise KeyError(obj)
            return self._names[obj]
        return super().__getitem__(obj)

    def __setitem__(self, key, obj):
        assert isinstance(obj, _Player)
        super().__setitem__(key, obj)
        self._names[obj.name] = obj

    def __repr__(self):
        return f"<PlayerLookup dictionary with {len(self.data)} items>"


class _Player:
    def __init__(self, ranking, profile_id, name, avatar_url):
        self.profile_id = profile_id
        self.name = name
        self.wins = 0
        self.losses = 0
        self.prv_rating = ranking.get_default_rating()
        self.rating = ranking.get_default_rating()
        self.avatar_url = avatar_url

    def update_rating(self, new_rating):
        self.prv_rating = self.rating
        self.rating = new_rating

    def __repr__(self):
        return f"<Player {self.name}, id={self.profile_id}>"

    @property
    def sql_row(self):
        return (
            self.profile_id,
            self.name,
            self.avatar_url,
            self.wins,
            self.losses,
            self.prv_rating.display_value,
            self.rating.display_value,
        )


class _OutCome:

    def __init__(self, result, p0, p1):
        self._hash = hashlib.sha256(result.filename.encode()).hexdigest()
        self._filename = result.filename
        self._start_time = result.start_time
        self._end_time = result.end_time
        self._p0_profile_id = p0.profile_id
        self._p1_profile_id = p1.profile_id
        self._p0_rating0 = p0.prv_rating
        self._p1_rating0 = p1.prv_rating
        self._p0_rating1 = p0.rating
        self._p1_rating1 = p1.rating
        self._p0_faction = result.player0.faction
        self._p1_faction = result.player1.faction
        self._p0_selected_faction = result.player0.selected_faction
        self._p1_selected_faction = result.player1.selected_faction
        self._map_uid = result.map_uid
        self._map_title = result.map_title

    @staticmethod
    def _sql_date_fmt(dt):
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    @property
    def sql_row(self):
        return (
            self._hash,
            self._sql_date_fmt(self._start_time),
            self._sql_date_fmt(self._end_time),
            self._filename,
            self._p0_profile_id,
            self._p1_profile_id,
            self._p0_rating0.display_value,
            self._p1_rating0.display_value,
            self._p0_rating1.display_value,
            self._p1_rating1.display_value,
            self._p0_faction,
            self._p1_faction,
            self._p0_selected_faction,
            self._p1_selected_faction,
            self._map_uid,
            self._map_title,
        )


def _get_players_outcomes(accounts_db, results, ranking_system):

    ranking = ranking_systems[ranking_system]()

    player_lookup = PlayerLookup(accounts_db, ranking)
    outcomes = []

    ratings = ranking.compute_ratings_from_series_of_games(results, player_lookup)

    for result, (r0, r1) in zip(results, ratings):
        p0 = player_lookup[result.player0]
        p1 = player_lookup[result.player1]
        p0.update_rating(r0)
        p1.update_rating(r1)
        p0.wins += 1
        p1.losses += 1
        outcomes.append(_OutCome(result, p0, p1))
    players = player_lookup.values()
    return players, outcomes


def _main(args):
    conn = sqlite3.connect(args.database)

    c = conn.cursor()

    # We don't know if the new submitted replays will be properly ordered, so
    # all the information needs to be reconstructed
    c.execute('DROP TABLE IF EXISTS players')
    c.execute('DROP TABLE IF EXISTS outcomes')

    with open(args.schema) as f:
        c.executescript(f.read())

    # Re-use the cached OpenRA account information to prevent stressing too
    # much the service
    request_accounts = c.execute('SELECT * FROM accounts')
    accounts_db = {fp: (pid, pname, avatar_url) for fp, pid, pname, avatar_url in request_accounts.fetchall()}

    results = get_results(accounts_db, args.replays, args.period)

    players, outcomes = _get_players_outcomes(accounts_db, results, args.ranking)

    outcomes_sql = [o.sql_row for o in outcomes]
    players_sql = [p.sql_row for p in players]
    accounts_sql = [(fp, acc[0], acc[1], acc[2]) for fp, acc in accounts_db.items()]

    c.executemany('INSERT OR IGNORE INTO accounts VALUES (?,?,?,?)', accounts_sql)
    c.executemany('INSERT OR IGNORE INTO players VALUES (?,?,?,?,?,?,?)', players_sql)
    c.executemany('INSERT OR IGNORE INTO outcomes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', outcomes_sql)

    conn.commit()
    conn.close()


def run():
    logging.basicConfig(level='INFO')
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database', default='db.sqlite3')
    parser.add_argument('-s', '--schema', default=op.join(op.dirname(__file__), 'ladder.sql'))
    parser.add_argument('-r', '--ranking', choices=ranking_systems.keys(), default='trueskill')
    parser.add_argument('-p', '--period')
    parser.add_argument('replays', nargs='*')
    args = parser.parse_args()

    lockfile = args.database + '.lock'
    lock = FileLock(lockfile, timeout=1)
    try:
        with lock:
            _main(args)
    except Timeout:
        logging.error('Another instance of this application currently holds the %s lock file.', lockfile)
