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
import yaml
from filelock import FileLock, Timeout

from .utils import get_results


class _Player:

    def __init__(self, profile_id, name, avatar_url, extra_info):
        self.profile_id = profile_id
        self.name = name
        self.avatar_url = avatar_url
        self.wins = 0
        self.losses = 0
        self.division = self._get_player_division(extra_info['Divisions'], profile_id)
        self.status = self._get_player_status(extra_info, profile_id)

    @staticmethod
    def _get_player_division(divisions, profile_id):
        for division, players in divisions.items():
            profile_ids = [p[0] for p in players]
            if profile_id in profile_ids:
                return division
        return None

    @staticmethod
    def _get_player_status(extra_info, profile_id):
        return 'SF' if profile_id in extra_info.get('Forfeit', []) else None

    @property
    def sql_row(self):
        return (
            self.profile_id,
            self.name,
            self.avatar_url,
            self.wins,
            self.losses,
            self.division,
            self.status,
        )


class _OutCome:

    def __init__(self, result, p0, p1):
        self._hash = hashlib.sha256(result.filename.encode()).hexdigest()
        self._filename = result.filename
        self._start_time = result.start_time
        self._end_time = result.end_time
        self._p0_profile_id = p0.profile_id
        self._p1_profile_id = p1.profile_id
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
    def profile_pair(self):
        return (self._p0_profile_id, self._p1_profile_id)

    @property
    def sql_row(self):
        return (
            self._hash,
            self._sql_date_fmt(self._start_time),
            self._sql_date_fmt(self._end_time),
            self._filename,
            self._p0_profile_id,
            self._p1_profile_id,
            self._p0_faction,
            self._p1_faction,
            self._p0_selected_faction,
            self._p1_selected_faction,
            self._map_uid,
            self._map_title,
        )


def _records_count(records, outcome):
    return len([r for r in records if outcome == r.profile_pair])


def _get_players_outcomes(accounts_db, results, players_info):

    profile2player = {}
    outcomes = []
    extra_outcomes = []

    # XXX: currently no sane way of querying profile names from profile IDs, so
    # there are hardcoded in the info file
    for division, players in players_info['Divisions'].items():
        for profile_id, profile_name in players:
            profile2player[profile_id] = _Player(profile_id, profile_name, '', players_info)

    for result in results:
        acc0 = accounts_db.get(result.player0.fingerprint)
        acc1 = accounts_db.get(result.player1.fingerprint)
        if acc0 is None or acc1 is None:
            continue
        pid0, p0_name, p0_avatar = acc0
        pid1, p1_name, p1_avatar = acc1
        p0 = profile2player.get(pid0)
        p1 = profile2player.get(pid1)
        if None in (p0, p1):  # players not registered
            continue
        # Replace hardcoded names with name obtained from the API
        p0.name = p0_name
        p1.name = p1_name
        # Replace empty avatars with the one obtained from the API
        p0.avatar_url = p0_avatar
        p1.avatar_url = p1_avatar
        if None in (p0.division, p1.division) or p0.division != p1.division:
            continue

        # Register playoffs (or whatever extra match) somewhere else
        if _records_count(outcomes, (pid0, pid1)) + _records_count(outcomes, (pid1, pid0)) == 2:
            extra_outcomes.append(_OutCome(result, p0, p1))
            continue

        # Register win/losses only if no special status
        if not any((p0.status, p1.status)):
            p0.wins += 1
            p1.losses += 1
        outcomes.append(_OutCome(result, p0, p1))

    players = profile2player.values()

    return players, outcomes, extra_outcomes


def _handle_extra_outcomes(c, outcomes, playoffs):
    playoff_outcomes_sql = [po.sql_row for po in outcomes]
    playoffs_sql = []

    for label, playoff_data in playoffs.items():
        bestof = playoff_data['bestof']
        players = playoff_data['players']
        assert len(players) in (2, 4)

        players_sql = [(label, player_id) for player_id in players]
        c.executemany('INSERT OR IGNORE INTO playoff_playersets VALUES (?,?)', players_sql)

        playoffs_sql.append((label, bestof))

    c.executemany('INSERT OR IGNORE INTO playoffs VALUES (?,?)', playoffs_sql)
    c.executemany('INSERT OR IGNORE INTO playoff_outcomes VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', playoff_outcomes_sql)


def _main(args):
    conn = sqlite3.connect(args.database)

    c = conn.cursor()

    # We don't know if the new submitted replays will be properly ordered, so
    # all the information needs to be reconstructed
    c.execute('DROP TABLE IF EXISTS players')
    c.execute('DROP TABLE IF EXISTS outcomes')

    c.execute('DROP TABLE IF EXISTS playoff_outcomes')
    c.execute('DROP TABLE IF EXISTS playoff_playersets')
    c.execute('DROP TABLE IF EXISTS playoffs')

    with open(args.schema) as f:
        c.executescript(f.read())

    # Re-use the cached OpenRA account information to prevent stressing too
    # much the service
    request_accounts = c.execute('SELECT * FROM accounts')
    accounts_db = {fp: (pid, pname, avatar_url) for fp, pid, pname, avatar_url in request_accounts.fetchall()}

    results = get_results(accounts_db, args.replays)

    with open(args.playersinfo) as f:
        players_info = yaml.safe_load(f)
    players, outcomes, extra_outcomes = _get_players_outcomes(accounts_db, results, players_info)

    outcomes_sql = [o.sql_row for o in outcomes]
    players_sql = [p.sql_row for p in players]
    accounts_sql = [(fp, acc[0], acc[1], acc[2]) for fp, acc in accounts_db.items()]

    c.executemany('INSERT OR IGNORE INTO accounts VALUES (?,?,?,?)', accounts_sql)
    c.executemany('INSERT OR IGNORE INTO players VALUES (?,?,?,?,?,?,?)', players_sql)
    c.executemany('INSERT OR IGNORE INTO outcomes VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', outcomes_sql)

    playoffs = players_info.get('Playoffs')
    if playoffs:
        _handle_extra_outcomes(c, extra_outcomes, playoffs)

    conn.commit()
    conn.close()


def run():
    logging.basicConfig(level='INFO')
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database', default='db.sqlite3')
    parser.add_argument('-s', '--schema', default=op.join(op.dirname(__file__), 'ragl.sql'))
    parser.add_argument('-p', '--playersinfo', default=op.join(op.dirname(__file__), 'ragl-s10.yml'))
    parser.add_argument('replays', nargs='*')
    args = parser.parse_args()

    lockfile = args.database + '.lock'
    lock = FileLock(lockfile, timeout=1)
    try:
        with lock:
            _main(args)
    except Timeout:
        logging.error('Another instance of this application currently holds the %s lock file.', lockfile)
