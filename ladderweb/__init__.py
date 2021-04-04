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

import colorsys
import os
import os.path as op
import json
import numpy as np
import sqlite3
import calendar
from datetime import date
from flask import (
    Flask,
    current_app,
    escape,
    g,
    jsonify,
    render_template,
    request,
    send_file,
    url_for,
)


# XXX: store in a file probably
_cfg = dict(
    min_datapoints=10,
    datapoints=50,
)


def _db_get(period=None):
    if 'db' not in g:
        period = 'all' if period is None else period
        dbname = f'db-{period}.sqlite3'
        db = op.join(app.instance_path, dbname)
        g.db = sqlite3.connect(db, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
    return g.db


def _db_close(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def create_app():
    app = Flask(__name__)
    app.teardown_appcontext(_db_close)
    return app


app = create_app()


@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = op.join(app.root_path, endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)


def _get_current_period():
    today = date.today()
    start_month = ((today.month - 1) & ~1) + 1
    end_month = start_month + 1
    _, end_day = calendar.monthrange(today.year, end_month)
    return dict(
        start=date(today.year, start_month, 1),
        end=date(today.year, end_month, end_day),
        duration='2 months',
    )


def _get_menu(cur_period=None, **args):
    ret = dict(
        pages=(
            ('leaderboard', url_for('leaderboard', period=cur_period), 'Leaderboard'),
            ('latest_games', url_for('latest_games', period=cur_period), 'Latest games'),
            ('globalstats', url_for('globalstats', period=cur_period), 'Global stats'),
            ('info', url_for('info'), 'Information'),
        ),
    )

    period_pages = {'leaderboard', 'latest_games', 'player', 'globalstats'}
    if request.endpoint in period_pages:
        ret['period'] = [
            dict(
                caption=caption,
                url=url_for(request.endpoint, period=period, **args),
                active=period == cur_period,
            ) for caption, period in (
                ('This period', '2m'),
                ('All time', None),
            )
        ]

    return ret


@app.route('/', defaults=dict(period=None))
@app.route('/period/<period>')
def leaderboard(period):
    menu = _get_menu(cur_period=period)
    ajax_url = url_for('leaderboard_js', period=period)
    return render_template(
        'leaderboard.html',
        navbar_menu=menu,
        ajax_url=ajax_url,
        period=period,
        period_info=_get_current_period(),
    )


@app.route('/leaderboard-js', defaults=dict(period=None))
@app.route('/leaderboard-js/period/<period>')
def leaderboard_js(period):
    db = _db_get(period)
    cur = db.execute('''SELECT * FROM players WHERE rating > 0 ORDER BY rating DESC''')

    rows = []
    for i, (profile_id, profile_name, avatar_url, wins, losses, prv_rating, rating) in enumerate(cur, 1):
        rows.append(dict(
            row_id=i,
            player=dict(
                name=escape(profile_name),
                url=url_for('player', profile_id=profile_id, period=period),
                avatar_url=avatar_url,
            ),
            rating=dict(
                value=rating,
                diff=rating - prv_rating,
            ),
            played=wins + losses,
            wins=wins,
            losses=losses,
            winrate=wins / (wins + losses) * 100,
        ))

    return jsonify(rows)


@app.route('/latest', defaults=dict(period=None))
@app.route('/latest/period/<period>')
def latest_games(period):
    menu = _get_menu(cur_period=period)
    ajax_url = url_for('latest_games_js', period=period)
    return render_template('latest.html', navbar_menu=menu, ajax_url=ajax_url)


@app.route('/latest-js', defaults=dict(period=None))
@app.route('/latest-js/period/<period>')
def latest_games_js(period):
    db = _db_get(period)
    cur = db.execute('''
        SELECT
            hash,
            end_time,
            strftime('%M:%S', julianday(end_time) - julianday(start_time)) AS duration,
            profile_id0,
            profile_id1,
            rating_0 - rating_0_prv AS diff0,
            rating_1 - rating_1_prv AS diff1,
            p0.profile_name AS p0_name,
            p1.profile_name AS p1_name,
            map_title
        FROM outcomes o
        LEFT JOIN players p0 ON p0.profile_id = o.profile_id0
        LEFT JOIN players p1 ON p1.profile_id = o.profile_id1
        ORDER BY o.end_time DESC
        '''
    )
    matches = cur.fetchall()
    cur.close()

    games = []
    for match in matches:
        game = dict(
            replay=dict(
                hash=match['hash'],
                url=url_for('replay', replay_hash=match['hash']),
            ),
            date=match['end_time'],
            duration=match['duration'],
            map=match['map_title'],
            p0=dict(
                name=escape(match['p0_name']),
                url=url_for('player', profile_id=match['profile_id0'], period=period),
                diff=match['diff0'],
            ),
            p1=dict(
                name=escape(match['p1_name']),
                url=url_for('player', profile_id=match['profile_id1'], period=period),
                diff=match['diff1'],
            ),
        )
        games.append(game)

    return jsonify(games)


def _scaled(a, m):
    n = len(a)
    nr = range(n)
    mr = [x * n / m for x in range(m)]
    return [round(x) for x in np.interp(mr, nr, a)]


def _get_player_ratings(db, profile_id):
    cur = db.execute('''
        SELECT
            profile_id0,
            profile_id1,
            rating_0,
            rating_1
        FROM outcomes o
        LEFT JOIN players p0 ON p0.profile_id = o.profile_id0
        LEFT JOIN players p1 ON p1.profile_id = o.profile_id1
        WHERE :pid IN (o.profile_id0, o.profile_id1)
        ORDER BY o.end_time''',
        dict(pid=profile_id)
    )
    ratings = []
    for match in cur:
        if match['profile_id0'] == profile_id:
            rating = match['rating_0']
        elif match['profile_id1'] == profile_id:
            rating = match['rating_1']
        else:
            continue  # XXX shouldn't happen, assert?
        ratings.append(rating)
    cur.close()

    ratings = ratings[_cfg['min_datapoints']:]
    if not ratings:
        return [], []

    datapoints = _cfg['datapoints']
    rating_labels = [str('') for x in range(datapoints)]
    rating_labels = json.dumps(rating_labels)

    ratings = _scaled(ratings, datapoints)  # rescale all ratings to a fixed number of data points
    rating_data = json.dumps(ratings)

    return dict(
        labels=rating_labels,
        data=rating_data,
    )


def _get_player_info(db, profile_id):
    cur = db.execute('''
        SELECT
        *, (
            SELECT COUNT(*)
            FROM players
            WHERE rating >= (SELECT rating FROM players WHERE profile_id=:pid)
        ) AS rank,
        (
            SELECT strftime('%M:%S', AVG(julianday(end_time) - julianday(start_time)))
            FROM outcomes
            WHERE :pid IN (profile_id0, profile_id1)
        ) AS avg_game_duration
        FROM players WHERE profile_id=:pid
        LIMIT 1''',
        dict(pid=profile_id)
    )
    player = cur.fetchone()
    cur.close()
    return player


def _get_player_faction_stats(db, profile_id):
    cur = db.execute('''
        SELECT COUNT(*)/2 AS count,
            (CASE
            WHEN o.profile_id0=:pid THEN selected_faction_0
            WHEN o.profile_id1=:pid THEN selected_faction_1
        END) AS faction
        FROM outcomes o LEFT JOIN players p ON p.profile_id IN (o.profile_id0, o.profile_id1)
        WHERE :pid IN (o.profile_id0, o.profile_id1)
        GROUP BY faction''',
        dict(pid=profile_id)
    )
    hist = [(r['faction'], r['count']) for r in cur]
    cur.close()
    faction_names, faction_data = zip(*hist)
    faction_colors = _get_colors(len(hist))
    return dict(
        names=list(faction_names),
        data=list(faction_data),
        total=sum(faction_data),
        colors=faction_colors,
    )


def _get_player_map_stats(db, profile_id):
    cur = db.execute('''
        SELECT COUNT(*) AS count, map_title FROM outcomes WHERE profile_id0=:pid GROUP BY map_title''',
        dict(pid=profile_id)
    )
    hist_wins = {r['map_title']: r['count'] for r in cur}
    cur.close()

    cur = db.execute('''
        SELECT -COUNT(*) AS count, map_title FROM outcomes WHERE profile_id1=:pid GROUP BY map_title''',
        dict(pid=profile_id)
    )
    hist_losses = {r['map_title']: r['count'] for r in cur}
    cur.close()

    map_names = sorted(list(set(hist_wins.keys()) | set(hist_losses.keys())))
    map_win_data = [hist_wins.get(m, 0) for m in map_names]
    map_loss_data = [hist_losses.get(m, 0) for m in map_names]
    return dict(
        names=map_names,
        win_data=map_win_data,
        loss_data=map_loss_data,
    )


@app.route('/player-games-js/<int:profile_id>', defaults=dict(period=None))
@app.route('/player-games-js/<int:profile_id>/period/<period>')
def player_games_js(profile_id, period):
    db = _db_get(period)
    cur = db.execute('''
        SELECT
            hash,
            end_time,
            strftime('%M:%S', julianday(end_time) - julianday(start_time)) AS duration,
            profile_id0,
            profile_id1,
            rating_0 - rating_0_prv AS diff0,
            rating_1 - rating_1_prv AS diff1,
            p0.profile_name AS p0_name,
            p1.profile_name AS p1_name,
            map_title
        FROM outcomes o
        LEFT JOIN players p0 ON p0.profile_id = o.profile_id0
        LEFT JOIN players p1 ON p1.profile_id = o.profile_id1
        WHERE :pid in (o.profile_id0, o.profile_id1)
        ORDER BY o.end_time DESC
        ''',
        dict(pid=profile_id)
    )
    games = []
    for match in cur:
        if match['profile_id0'] == profile_id:
            diff = match['diff0']
            opponent = escape(match['p1_name'])
            opponent_id = match['profile_id1']
            outcome = 'Won'
        elif match['profile_id1'] == profile_id:
            diff = match['diff1']
            opponent = escape(match['p0_name'])
            opponent_id = match['profile_id0']
            outcome = 'Lost'
        else:
            continue  # XXX shouldn't happen, assert?
        game = dict(
            date=match['end_time'],
            opponent=dict(
                name=opponent,
                url=url_for('player', profile_id=opponent_id, period=period),
                #avatar_url=avatar_url,
            ),
            map=match['map_title'],
            outcome=dict(
                desc=outcome,
                diff=diff,
            ),
            duration=match['duration'],
            replay=dict(
                hash=match['hash'],
                url=url_for('replay', replay_hash=match['hash']),
            ),
        )
        games.append(game)
    cur.close()

    return jsonify(games)


@app.route('/player/<int:profile_id>', defaults=dict(period=None))
@app.route('/player/<int:profile_id>/period/<period>')
def player(profile_id, period):
    db = _db_get(period)
    menu = _get_menu(cur_period=period, profile_id=profile_id)

    player = _get_player_info(db, profile_id)
    if not player:
        return render_template('noplayer.html', navbar_menu=menu, profile_id=profile_id)

    ajax_url = url_for('player_games_js', profile_id=profile_id, period=period)
    return render_template(
        'player.html',
        navbar_menu=menu,
        player=player,
        ajax_url=ajax_url,
        rating_stats=_get_player_ratings(db, profile_id),
        faction_stats=_get_player_faction_stats(db, profile_id),
        map_stats=_get_player_map_stats(db, profile_id),
    )


def _hexc(fc):
    return '#' + ''.join('%02X' % int(fc[i] * 255) for i in range(3))


def _get_colors(n):
    return [_hexc(colorsys.hls_to_rgb(i / n, .4, .6)) for i in range(n)]


def _get_global_faction_stats(db):
    hist = {}

    # XXX: clumsy, patch welcome
    for i in range(2):
        cur = db.execute(f'SELECT COUNT(*) AS count, selected_faction_{i} AS faction FROM outcomes GROUP BY selected_faction_{i}')
        hist.update({r['faction']: r['count'] for r in cur})
        cur.close()
    hist = hist.items()

    if not hist:
        return [], [], []

    faction_names, faction_data = zip(*hist)
    faction_colors = _get_colors(len(hist))
    return dict(
        names=list(faction_names),
        data=list(faction_data),
        total=sum(faction_data),
        colors=faction_colors,
    )


def _get_global_map_stats(db):
    cur = db.execute('SELECT COUNT(*) AS count, map_title FROM outcomes GROUP BY map_title')
    hist = [(r['map_title'], r['count']) for r in cur]
    cur.close()

    if not hist:
        return [], [], []

    map_names, map_data = zip(*hist)
    map_colors = _get_colors(len(hist))
    return dict(
        names=list(map_names),
        data=list(map_data),
        total=sum(map_data),
        colors=map_colors,
    )


@app.route('/globalstats', defaults=dict(period=None))
@app.route('/globalstats/period/<period>')
def globalstats(period):
    db = _db_get(period)

    cur = db.execute('''
        SELECT
            COUNT(*) AS nb_games,
            strftime('%M:%S', AVG(julianday(end_time) - julianday(start_time))) AS avg_duration
        FROM outcomes'''
    )
    data = cur.fetchone()
    nb_games = data['nb_games']
    avg_duration = data['avg_duration']
    cur.close()

    cur = db.execute('SELECT COUNT(*) AS nb_players FROM players')
    nb_players = cur.fetchone()['nb_players']
    cur.close()

    menu = _get_menu(cur_period=period)
    return render_template(
        'globalstats.html',
        navbar_menu=menu,
        faction_stats=_get_global_faction_stats(db),
        map_stats=_get_global_map_stats(db),
        nb_games=nb_games,
        nb_players=nb_players,
        avg_duration=avg_duration,
    )


@app.route('/about')
@app.route('/info')
def info():
    menu = _get_menu()
    return render_template('info.html', navbar_menu=menu, period_info=_get_current_period())


@app.route('/replay/<replay_hash>')
def replay(replay_hash):
    db = _db_get()
    cur = db.execute('SELECT filename FROM outcomes WHERE hash=:hash', dict(hash=replay_hash))
    fullpath = cur.fetchone()['filename']
    cur.close()
    return send_file(fullpath, as_attachment=True)
