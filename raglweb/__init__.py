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

import os.path as op

import sqlite3
from flask import (
    Flask,
    current_app,
    g,
    render_template,
    send_file,
)


def _db_get():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'],
                               detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
    return g.db


def _db_close(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=op.join(app.instance_path, 'db.sqlite3'),
    )
    app.teardown_appcontext(_db_close)
    return app


app = create_app()


@app.route('/')
def scoreboards():
    db = _db_get()
    cur = db.execute('''
        SELECT
            profile_id,
            profile_name,
            wins,
            losses,
            division,
            status
        FROM players
        ORDER BY division, wins DESC
        '''
    )

    scoreboards = {}
    for profile_id, profile_name, wins, losses, division, status in cur:
        rows = scoreboards.get(division, [])
        nb_played = wins + losses
        rows.append(dict(
            row_id=len(rows) + 1,
            profile_id=profile_id,
            name=profile_name,
            played=wins + losses,
            wins=wins,
            losses=losses,
            winrate=wins / nb_played * 100 if nb_played else 0,
            status=status or '',
        ))
        scoreboards[division] = rows

    return render_template('scoreboards.html', scoreboards=scoreboards)


@app.route('/games')
def games():
    db = _db_get()
    cur = db.execute('''
        SELECT
            hash,
            end_time,
            profile_id0,
            profile_id1,
            p0.profile_name as p0_name,
            p1.profile_name as p1_name,
            map_title
        FROM outcomes o
        LEFT JOIN players p0 ON p0.profile_id = o.profile_id0
        LEFT JOIN players p1 ON p1.profile_id = o.profile_id1
        ORDER BY o.end_time DESC'''
    )
    matches = cur.fetchall()
    cur.close()

    games = []
    for match in matches:
        game = dict(
            hash=match['hash'],
            date=match['end_time'],
            map=match['map_title'],
            p0=match['p0_name'],
            p1=match['p1_name'],
            p0_id=match['profile_id0'],
            p1_id=match['profile_id1'],
        )
        games.append(game)

    return render_template('games.html', games=games)


def _get_player_info(db, profile_id):
    cur = db.execute('''
        SELECT
            profile_name,
            division
        FROM players
        WHERE profile_id = :pid
        LIMIT 1''',
        dict(pid=profile_id)
    )
    row = cur.fetchone()
    player_info = dict(
        profile_name = row['profile_name'],
        division = row['division']
    )
    cur.close()
    return player_info


def _get_player_records(db, profile_id):
    cur = db.execute('''
        SELECT
            hash,
            end_time,
            profile_id0,
            profile_id1,
            p0.profile_name as p0_name,
            p1.profile_name as p1_name,
            map_title
        FROM outcomes o
        LEFT JOIN players p0 ON p0.profile_id = o.profile_id0
        LEFT JOIN players p1 ON p1.profile_id = o.profile_id1
        WHERE :pid in (o.profile_id0, o.profile_id1)
        ORDER BY o.end_time DESC''',
        dict(pid=profile_id)
    )
    records = {}
    for match in cur:
        if match['profile_id0'] == profile_id:
            opponent = match['p1_name']
            opponent_id = match['profile_id1']
            outcome = 'Won'
        elif match['profile_id1'] == profile_id:
            opponent = match['p0_name']
            opponent_id = match['profile_id0']
            outcome = 'Lost'
        else:
            assert False

        game = dict(
            opponent=opponent,
            opponent_id=opponent_id,
            date=match['end_time'],
            map=match['map_title'],
            outcome=outcome,
            hash=match['hash'],
        )

        games = records.get(opponent_id, [])
        games.append(game)
        records[opponent_id] = games[:2]  # XXX: cap to 2 for now

    cur.close()

    return records


def _get_player_opponents(db, profile_id, division):
    cur = db.execute('''
        SELECT
            profile_id,
            profile_name
        FROM players
        WHERE
            profile_id != :pid AND
            division = :division AND
            status IS NULL
        ORDER BY profile_name COLLATE NOCASE
        ''',
        dict(pid=profile_id, division=division)
    )

    for row in cur:
        yield dict(
            opponent_id=row['profile_id'],
            opponent=row['profile_name'],
        )

    cur.close()


@app.route('/player/<int:profile_id>')
def player(profile_id):
    db = _db_get()

    player_info = _get_player_info(db, profile_id)
    records = _get_player_records(db, profile_id)
    opponents = _get_player_opponents(db, profile_id, player_info['division'])

    # Complete opponent information with potential records
    matches = []
    for opponent in opponents:
        games = records.get(opponent['opponent_id'], [])
        opponent['games'] = games
        opponent['status'] = '✅ All matches played' if len(games) == 2 else '🕒 Pending'
        matches.append(opponent)

    return render_template('player.html', player=player_info, matches=matches)


@app.route('/replay/<replay_hash>')
def replay(replay_hash):
    db = _db_get()
    cur = db.execute('SELECT filename FROM outcomes WHERE hash=:hash', dict(hash=replay_hash))
    fullpath = cur.fetchone()['filename']
    cur.close()
    return send_file(fullpath, as_attachment=True)
