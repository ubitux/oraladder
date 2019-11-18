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
import argparse
import logging
import struct
from datetime import datetime

from . import miniyaml


class GamePlayerInfo:

    def __init__(self, fingerprint, display_name, faction, selected_faction):
        self.fingerprint = fingerprint
        self.display_name = display_name
        self.faction = faction
        self.selected_faction = selected_faction

    def __str__(self):
        return self.display_name


class GameResult:

    def __init__(self, start_time, end_time, filename, player0, player1, map_uid, map_title):
        self.start_time = start_time
        self.end_time = end_time
        self.filename = filename
        self.player0 = player0
        self.player1 = player1
        self.map_uid = map_uid
        self.map_title = map_title

    def __str__(self):
        return f'{self.filename}: {self.player0} wins vs {self.player1}'


def _parse_date_fmt(date_string):
    return datetime.strptime(date_string, '%Y-%m-%d %H-%M-%S')


def _parse_fmt(data, fmt):
    n = struct.calcsize(fmt)
    return struct.unpack('<' + fmt, data[:n])


def _read_data_fmt(reader, fmt):
    n = struct.calcsize(fmt)
    data = reader.read(n)
    assert len(data) == n
    return _parse_fmt(data, fmt)


def _parse_game_info(input_file):
    # TODO: check file size
    input_file.seek(-8, 2)
    length, end_marker = _read_data_fmt(input_file, 'ii')
    if end_marker != -2:
        raise Exception(f'Invalid end marker {end_marker}')
    input_file.seek(-(length + 16), 1)
    start_marker, version = _read_data_fmt(input_file, 'ii')
    if start_marker != -1:
        raise Exception(f'Invalid start marker {start_marker}')
    game_data = input_file.read(length)
    length2, = _parse_fmt(game_data, 'i')
    assert length2 == length - 4
    game_yaml = game_data[4:]
    return miniyaml.load(game_yaml)


def get_result(filename):

    with open(filename, 'rb') as f:
        game_info = _parse_game_info(f)

        root_info = game_info['Root']
        start_time = _parse_date_fmt(root_info['StartTimeUtc'])
        end_time = _parse_date_fmt(root_info['EndTimeUtc'])
        map_uid = root_info['MapUid']
        map_title = root_info['MapTitle']

        players = [k for k in game_info.keys() if k.startswith('Player@')]
        if len(players) != 2:
            raise Exception(f"game doesn't have 2 but {len(players)} players")
        player0, player1 = [game_info[f'Player@{i}'] for i in range(2)]
        p0_name, p0_outcome, p0_fingerprint = player0['Name'], player0['Outcome'], player0['Fingerprint']
        p1_name, p1_outcome, p1_fingerprint = player1['Name'], player1['Outcome'], player1['Fingerprint']

        p0_faction = player0['FactionName']
        p1_faction = player1['FactionName']
        p0_selected_faction = player0.get('DisplayFactionName')
        p1_selected_faction = player1.get('DisplayFactionName')
        if None in (p0_selected_faction, p1_selected_faction):
            p0_selected_faction = 'Any' if player0['IsRandomFaction'] == 'True' else p0_faction
            p1_selected_faction = 'Any' if player1['IsRandomFaction'] == 'True' else p1_faction

        if not p0_fingerprint or not p1_fingerprint:
            p0_auth = 'yes' if p0_fingerprint else 'no'
            p1_auth = 'yes' if p1_fingerprint else 'no'
            raise Exception(f'not all players are authenticated ({p0_name}: {p0_auth}, {p1_name}: {p1_auth})')

        if p0_fingerprint == p1_fingerprint:
            raise Exception(f'player {p0_name} and {p1_name} are the same player')

        pA = GamePlayerInfo(p0_fingerprint, p0_name, p0_faction, p0_selected_faction)
        pB = GamePlayerInfo(p1_fingerprint, p1_name, p1_faction, p1_selected_faction)

        if (p0_outcome, p1_outcome) == ('Won', 'Lost'):
            p0 = pA
            p1 = pB
        elif (p1_outcome, p0_outcome) == ('Won', 'Lost'):
            p0 = pB
            p1 = pA
        else:
            if p0_outcome != p1_outcome:
                raise Exception(f'game result is half set: {p0_outcome} / {p1_outcome}')

            p0_disconnect = int(player0.get('DisconnectFrame', 0))
            p1_disconnect = int(player1.get('DisconnectFrame', 0))
            if not p0_disconnect or not p1_disconnect:
                raise Exception(f'invalid disconnect frames {p0_disconnect} / {p1_disconnect}')

            if p0_disconnect > p1_disconnect:
                p0 = pA
                p1 = pB
            elif p0_disconnect < p1_disconnect:
                p0 = pB
                p1 = pA
            else:
                raise Exception(f'players disconnected at the same time ({p0_disconnect}), draw')

        return GameResult(start_time, end_time, op.basename(filename), p0, p1, map_uid, map_title)


def _log_result(filename):
    try:
        result = get_result(filename)
    except Exception as e:
        logging.error(f'{op.basename(filename)}: {e}')
    else:
        logging.info(result)


def _main(args):
    logging.basicConfig(level='INFO', format='%(message)s')
    for filename in sorted(args.replays):
        if op.isdir(filename):
            for root, dirs, files in os.walk(filename):
                for name in files:
                    _log_result(op.join(root, name))
        else:
            _log_result(filename)


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('replays', nargs='+')
    args = parser.parse_args()
    _main(args)
