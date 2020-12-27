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

import argparse
import hashlib
import json
import logging
import os
import os.path as op
import tempfile
import urllib.request
import zipfile


def _query_maps_info(map_ids):
    map_ids = ','.join(map_ids)
    map_url = f'https://resource.openra.net/map/id/{map_ids}'
    with urllib.request.urlopen(map_url) as response:
        return json.loads(response.read())


def _get_maps(mapsdir):
    '''
    Compute local map hashes.
    Return a dict mapping the hash to the local filename path.
    '''

    maps = {}
    for map_fname in os.listdir(mapsdir):
        if not map_fname.endswith('.oramap'):
            continue
        map_path = op.join(mapsdir, map_fname)
        with zipfile.ZipFile(map_path) as map_zfile:
            m = hashlib.sha1()
            for name in map_zfile.namelist():
                _, ext = op.splitext(name)
                if ext not in {'.yaml', '.bin', '.lua'}:
                    continue
                with map_zfile.open(name) as f:
                    m.update(f.read())
            maps[m.hexdigest()] = map_path
    return maps


def _get_map_ids_from_file(maps_file_path):
    with open(maps_file_path) as f:
        return [line.strip() for line in f.readlines()]


def download_maps(directory, maps_file):
    if not op.exists(directory):
        os.makedirs(directory)

    map_ids = _get_map_ids_from_file(maps_file)
    local_maps = _get_maps(directory)
    map_hashes = []
    if map_ids:
        data = _query_maps_info(map_ids)
        for map_info in data:
            map_hash = map_info['map_hash']
            map_title = map_info['title']
            map_hashes.append(map_hash)
            if map_hash in local_maps:
                logging.info('Already available Map %s "%s": %s', map_hash, map_title, local_maps[map_hash])
            else:
                map_url = map_info['url']
                # XXX: can we do that in one request instead of 2?
                req = urllib.request.Request(map_url, method='HEAD')
                map_fname = urllib.request.urlopen(req).info().get_filename()
                map_path = op.join(directory, map_fname)
                logging.info('Downloading Map %s "%s": %s', map_hash, map_title, map_path)
                urllib.request.urlretrieve(map_url, filename=map_path)
                local_maps[map_hash] = map_path

    return [local_maps[h] for h in map_hashes]


def _create_pack(zipname, map_files, prefix):
    if op.exists(zipname):
        os.remove(zipname)
    logging.info('Creating %s', zipname)
    with zipfile.ZipFile(zipname, 'w') as pack_zfile:
        for map_file in map_files:
            arcname = op.join(prefix, op.basename(map_file))
            pack_zfile.write(map_file, arcname)


def run():
    logging.basicConfig(level='INFO')
    parser = argparse.ArgumentParser()
    parser.add_argument('maps_file')
    parser.add_argument('--pack')
    parser.add_argument('--prefix', default='maps')
    parser.add_argument('--download-dir', default=op.join(tempfile.gettempdir(), 'ora-mapstool'))
    args = parser.parse_args()

    map_files = download_maps(args.download_dir, args.maps_file)
    if args.pack:
        _create_pack(args.pack, map_files, args.prefix)
