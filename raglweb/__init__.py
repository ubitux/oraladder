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
import sqlite3
from datetime import date, datetime, timedelta

from flask import (
    Flask,
    current_app,
    g,
    render_template,
    send_file,
    jsonify,
)

from .forfeit_games import (
    get_player_forfeit_games,
    get_forfeit_win_loss_stats,
)
from .playoffs import get_playoff2, get_playoff4, PlayoffOutcome


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


def _ordered_alphanumerically(x: str, y: str) -> bool:
    # returns True if x is the alphanumerically higher-ranked string,
    # i.e. "abcde" before "efgh"
    return x.lower() < y.lower()


def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=op.join(app.instance_path, 'db-ragl.sqlite3'),
    )
    cfg_file = os.environ.get('RAGL_CONFIG', op.join(app.instance_path, 'ragl_config.py'))
    app.config.from_pyfile(cfg_file)
    app.teardown_appcontext(_db_close)
    return app


app = create_app()


@app.route('/')
def scoreboards():
    db = _db_get()

    cur = db.execute('''
        SELECT
            COUNT(profile_id) as nb_profiles,
            division
        FROM players
        WHERE status IS NULL
        GROUP BY division
        '''
    )

    matchup_count = app.config['GAMES_PER_MATCH']
    max_matches = {row['division']: (row['nb_profiles'] - 1) * matchup_count for row in cur}

    cur = db.execute('''
        SELECT
            profile_id,
            profile_name,
            avatar_url,
            wins,
            losses,
            division,
            status
        FROM players
        ORDER BY division, status, wins DESC
        '''
    )

    forfeit_games = get_forfeit_win_loss_stats(db)

    scoreboards = {}
    for profile_id, profile_name, avatar_url, wins, losses, division, status in cur:
        rows = scoreboards.get(division, [])
        forfeit_wins = forfeit_games[profile_id]['wins']
        forfeit_losses = forfeit_games[profile_id]['losses']
        nb_played = wins + forfeit_wins + losses + forfeit_losses
        if status == 'SF':
            status = '⛔ Season Forfeit'
        elif nb_played == max_matches[division]:
            status = '✅ All matchups completed'
        else:
            status = ''  # TODO: handle late status

        rows.append(dict(
            profile_id=profile_id,
            name=profile_name,
            avatar_url=avatar_url,
            played=nb_played,
            max_matches=max_matches[division],
            wins=wins + forfeit_wins,
            losses=losses + forfeit_losses,
            winrate=(wins + forfeit_wins) / nb_played * 100 if nb_played else 0,
            status=status or '',
        ))

        # Take into account forfeit games when sorting the list
        rows = sorted(rows, key=lambda row: (row["wins"], row["winrate"]), reverse=True)
        # Set player rank based on sorted list
        for i, r in enumerate(rows, 1):
            r['row_id'] = 'SF' if "Season Forfeit" in r['status'] else i

        scoreboards[division] = rows

    return render_template('scoreboards.html', scoreboards=scoreboards)


def _get_games(db, outcomes_table, order='DESC'):
    cur = db.execute(f'''
        SELECT
            hash,
            end_time,
            profile_id0,
            profile_id1,
            p0.profile_name as p0_name,
            p1.profile_name as p1_name,
            map_title
        FROM {outcomes_table} o
        LEFT JOIN players p0 ON p0.profile_id = o.profile_id0
        LEFT JOIN players p1 ON p1.profile_id = o.profile_id1
        ORDER BY o.end_time {order}'''
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

    return games


@app.route('/playoffs')
def playoffs():
    db = _db_get()
    games = _get_games(db, 'playoff_outcomes', order='ASC')

    outcomes = [PlayoffOutcome((g['p0_id'], g['p0']), (g['p1_id'], g['p1'])) for g in games]

    cur = db.execute('SELECT label, bestof FROM playoffs')
    playoffs = cur.fetchall()
    cur.close()

    playoffs_data = []

    for playoff in playoffs:
        cur = db.execute('''
            SELECT
                pp.profile_id as id,
                p.profile_name as name
            FROM playoff_playersets pp
            LEFT JOIN players p ON p.profile_id = pp.profile_id
            WHERE pp.playoff_id=:label
        ''', dict(label=playoff['label']))
        players = [(r['id'], r['name']) for r in cur]
        cur.close()

        if len(players) == 4:
            matchups = get_playoff4(playoff['bestof'], players, outcomes)
        elif len(players) == 2:
            matchups = get_playoff2(playoff['bestof'], players, outcomes)
        else:
            assert False

        playoffs_data.append(dict(
            label=playoff['label'],
            bestof=playoff['bestof'],
            matchups=matchups,
        ))

    return render_template('playoffs.html', games=games, playoffs=playoffs_data)


@app.route('/games')
def games():
    db = _db_get()
    games = _get_games(db, 'outcomes')

    # create an unspoiled list of games (players ordered alphanumerically, additional "winner" attribute)
    for game in games:
        p0, p0_id, p1, p1_id = game['p0'], game['p0_id'], game['p1'], game['p1_id']
        # re-order players alphanumerically if necessary
        if not _ordered_alphanumerically(p0, p1):
            game.update(p0=p1, p0_id=p1_id, p1=p0, p1_id=p0_id)
        game['winner'] = p0

    return render_template('games.html', games=games)


@app.route('/games/json')
def games_json():
    db = _db_get()
    games = _get_games(db, 'playoff_outcomes')
    games += _get_games(db, 'outcomes')
    return jsonify(games)


def _get_player_info(db, profile_id):
    cur = db.execute('''
        SELECT
            profile_name,
            avatar_url,
            division,
            status
        FROM players
        WHERE profile_id = :pid
        LIMIT 1''',
        dict(pid=profile_id)
    )
    row = cur.fetchone()
    player_info = dict(
        profile_name=row['profile_name'],
        avatar_url=row['avatar_url'],
        division=row['division'],
        status=row['status'],
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
        ORDER BY o.end_time ASC''',
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
            date=datetime.fromisoformat(match['end_time']).strftime('%Y-%m-%d'),
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
            profile_name,
            status
        FROM players
        WHERE
            profile_id != :pid AND
            division = :division
        ORDER BY profile_name COLLATE NOCASE
        ''',
        dict(pid=profile_id, division=division)
    )

    for row in cur:
        yield dict(
            opponent_id=row['profile_id'],
            opponent=row['profile_name'],
            status=row['status'],
        )

    cur.close()


@app.route('/player/<int:profile_id>')
def player(profile_id):
    db = _db_get()

    player_info = _get_player_info(db, profile_id)
    records = _get_player_records(db, profile_id)
    records = records | get_player_forfeit_games(db, profile_id)
    opponents = _get_player_opponents(db, profile_id, player_info['division'])

    cfg = app.config

    # Complete opponent information with potential records
    matches = []
    matchup_count, matchup_done_count = 0, 0
    for opponent in opponents:
        games = records.get(opponent['opponent_id'], [])
        matchup_done = len(games) == cfg['GAMES_PER_MATCH']
        opponent['games'] = games
        if 'SF' in (player_info['status'], opponent['status']):
            opponent['status'] = '⛔ Canceled'
        else:
            opponent['status'] = '✅ All matches played' if matchup_done else '🕒 Pending'
            matchup_done_count += matchup_done
            matchup_count += 1
        matches.append(opponent)

    group_stage_end_time = cfg['START_TIME'] + timedelta(weeks=cfg['GROUP_STAGE_WEEKS'])
    # Calculate the fraction of the group stage that's complete.
    group_stage_completion = min(1, max(0, (date.today() - cfg['START_TIME']) / (group_stage_end_time - cfg['START_TIME'])))

    matchup_expected_done = int(matchup_count * group_stage_completion)

    if player_info['status'] == 'SF':
        status = '⛔ Season Forfeit'
    elif matchup_count == matchup_done_count:
        status = '✅ All matchups completed'
    elif matchup_expected_done > matchup_done_count:
        status = f'⚠️ Late by {matchup_expected_done-matchup_done_count} matchup(s): ' \
                 f'{matchup_expected_done}/{matchup_count} matchup(s) expected done by now'
    else:
        status = '🟢 In time'

    player = dict(
        profile_name=player_info['profile_name'],
        avatar_url=player_info['avatar_url'],
        status=status,
        matchup_done_count=matchup_done_count,
        matchup_count=matchup_count,
        start_time=app.config['START_TIME'],
        end_time=group_stage_end_time,
    )

    return render_template('player.html', player=player, matches=matches)


@app.route('/info')
def info():
    map_pack_version = app.config['MAP_PACK_VERSION']
    return render_template(
        'info.html',
        map_pack_file=f'ragl-map-pack-{map_pack_version}.zip',
        cfg=app.config,
    )


def _make_division_prefix(division_title):
    """Convert human readable division title into prefix to use in filename."""
    words = division_title.upper().split()
    division_prefix = words[0]
    if division_prefix.endswith('S'):
        division_prefix = division_prefix[:-1]
    division_prefix += ''.join(word[0] for word in words[1:])
    season = app.config['SEASON']
    prefix = f'RAGL-S{season:02d}-{division_prefix}-'
    return prefix


@app.route('/replay/<replay_hash>')
def replay(replay_hash):
    db = _db_get()
    cur = db.execute('''
        SELECT
            filename,
            p0.division as p0_division,
            p1.division as p1_division
        FROM outcomes o
        LEFT JOIN players p0 ON p0.profile_id = o.profile_id0
        LEFT JOIN players p1 ON p1.profile_id = o.profile_id1
        WHERE hash=:hash
    ''', dict(hash=replay_hash))
    row = cur.fetchone()

    p0_division = row['p0_division']
    p1_division = row['p1_division']
    assert p0_division == p1_division
    prefix = _make_division_prefix(p0_division)

    fullpath = row['filename']
    original_filename = op.basename(fullpath)
    attachment_filename = prefix + original_filename
    cur.close()
    return send_file(
        fullpath,
        as_attachment=True,
        attachment_filename=attachment_filename
    )


@app.route('/replay_playoff/<replay_hash>')
def replay_playoff(replay_hash):
    db = _db_get()
    cur = db.execute(f'''
        SELECT filename
        FROM playoff_outcomes o
        LEFT JOIN players p0 ON p0.profile_id = o.profile_id0
        LEFT JOIN players p1 ON p1.profile_id = o.profile_id1
        WHERE hash=:hash
    ''', dict(hash=replay_hash))
    row = cur.fetchone()

    season = app.config['SEASON']
    prefix = f'RAGL-S{season:02d}-PLAYOFF-'

    fullpath = row['filename']
    original_filename = op.basename(fullpath)
    attachment_filename = prefix + original_filename
    cur.close()
    return send_file(
        fullpath,
        as_attachment=True,
        attachment_filename=attachment_filename
    )
