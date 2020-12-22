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
        )
        games.append(game)

    return render_template('games.html', games=games)


@app.route('/replay/<replay_hash>')
def replay(replay_hash):
    db = _db_get()
    cur = db.execute('SELECT filename FROM outcomes WHERE hash=:hash', dict(hash=replay_hash))
    fullpath = cur.fetchone()['filename']
    cur.close()
    return send_file(fullpath, as_attachment=True)
