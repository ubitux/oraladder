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
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
from filelock import FileLock

from laddertools.mapstool import download_maps
from laddertools.utils import get_profile_ids


def _download_openra_sources(tmpdir, repo, version):
    '''
    Download OpenRA source code at specified version.
    '''

    release_tarball = f'{version}.tar.gz'
    release_tarball_path = op.join(tmpdir, release_tarball)
    if not op.exists(release_tarball_path):
        release_tarball_url = f'{repo}/archive/{release_tarball}'
        logging.info('Downloading %s', release_tarball_url)
        urllib.request.urlretrieve(release_tarball_url, filename=release_tarball_path)
    return release_tarball_path


def _prepare_openra_sources(tmpdir, version, release_tarball_path):
    '''
    Extract, patch and build OpenRA.
    '''

    srcdir = op.join(tmpdir, f'OpenRA-{version}')
    if not op.exists(srcdir):

        # Extract sources
        logging.info('Extracting %s', release_tarball_path)
        tar = tarfile.open(release_tarball_path)
        tar.extractall(tmpdir)
        tar.close()

        # Using Server.Map="" doesn't work for selecting a random map because it will
        # filter only maps in the "Conquest" category (RAGL maps typically aren't), so
        # we use this workaround instead for now
        map_cache_file = op.join(srcdir, 'OpenRA.Game/Map/MapCache.cs')
        content = ''
        with open(map_cache_file) as f:
            for line in f:
                if '"Conquest"' in line:
                    logging.info('Patching %s', map_cache_file)
                    f.readline()  # skip also the following line
                    continue
                content += line
        with open(map_cache_file, 'w') as f:
            f.write(content)

        # Build
        logging.info('Building OpenRA in %s', srcdir)
        subprocess.run(['make', '-C', srcdir, 'version', f'VERSION={version}'])
        subprocess.run(['make', '-C', srcdir])

    return srcdir


def _setup_sources(args):
    '''
    Setup the base sources and maps (everything that's common between
    isntances).
    '''
    lockfile = op.join(tempfile.gettempdir(), 'ora-srvwrap.lock')

    # This part of the setup is common to all spawned instances, so we protect
    # it under a lock
    with FileLock(lockfile):
        tmpdir = op.join(tempfile.gettempdir(), 'ora-srvwrap')
        mapsdir = op.join(tmpdir, 'maps', args.mod)
        map_paths = download_maps(mapsdir, args.maps_file)
        release_tarball_path = _download_openra_sources(tmpdir, args.repo, args.version)
        base_src_dir = _prepare_openra_sources(tmpdir, args.version, release_tarball_path)
        return base_src_dir, map_paths


_overrides = dict(
    ra='''
Player:
	Shroud:
		ExploredMapCheckboxEnabled: true
		ExploredMapCheckboxLocked: true
		FogCheckboxEnabled: true
		FogCheckboxLocked: true
	PlayerResources:
		DefaultCash: 5000
		DefaultCashDropdownLocked: true
	DeveloperMode:
		CheckboxEnabled: false
		CheckboxLocked: true
	LobbyPrerequisiteCheckbox@GLOBALBOUNTY:
		Enabled: true
		Locked: false
	LobbyPrerequisiteCheckbox@REUSABLEENGINEERS:
		Enabled: true
		Locked: false
	LobbyPrerequisiteCheckbox@GLOBALFACTUNDEPLOY:
		Enabled: true
		Locked: true

World:
	CrateSpawner:
		CheckboxEnabled: false
		CheckboxLocked: true
	MapBuildRadius:
		AllyBuildRadiusCheckboxEnabled: true
		AllyBuildRadiusCheckboxLocked: true
		BuildRadiusCheckboxEnabled: true
		BuildRadiusCheckboxLocked: true
	MapOptions:
		ShortGameCheckboxEnabled: true
		ShortGameCheckboxLocked: true
		TechLevel: unrestricted
		TechLevelDropdownLocked: true
		GameSpeed: default
		GameSpeedDropdownLocked: true
	MPStartLocations:
		SeparateTeamSpawnsCheckboxEnabled: true
		SeparateTeamSpawnsCheckboxLocked: true
	SpawnMPUnits:
		StartingUnitsClass: none
		DropdownLocked: true
	TimeLimitManager:
		TimeLimitLocked: true
''',
    cnc='''
Player:
	Shroud:
		ExploredMapCheckboxEnabled: true
		ExploredMapCheckboxLocked: true
		FogCheckboxEnabled: true
		FogCheckboxLocked: true
	PlayerResources:
		DefaultCash: 7500
		DefaultCashDropdownLocked: true
	DeveloperMode:
		CheckboxEnabled: false
		CheckboxLocked: true
	LobbyPrerequisiteCheckbox@GLOBALC17STEALTH
		Enabled: true
		Locked: true
	LobbyPrerequisiteCheckbox@GLOBALFACTUNDEPLOY:
		Enabled: true
		Locked: true

World:
	CrateSpawner:
		CheckboxEnabled: false
		CheckboxLocked: true
	MapBuildRadius:
		AllyBuildRadiusCheckboxEnabled: true
		AllyBuildRadiusCheckboxLocked: true
		BuildRadiusCheckboxEnabled: true
		BuildRadiusCheckboxLocked: true
	MapOptions:
		ShortGameCheckboxEnabled: true
		ShortGameCheckboxLocked: true
		TechLevel: unrestricted
		TechLevelDropdownLocked: true
		GameSpeed: default
		GameSpeedDropdownLocked: true
	MPStartLocations:
		SeparateTeamSpawnsCheckboxEnabled: true
		SeparateTeamSpawnsCheckboxLocked: true
	SpawnMPUnits:
		StartingUnitsClass: none
		DropdownLocked: true
	TimeLimitManager:
		TimeLimitLocked: true
'''
)


def _patched_rules(mod, mod_file_path, overrides_rel_path):
    mod_file_content = ''
    with open(mod_file_path) as f:
        for line in f:
            mod_file_content += line
            if line.startswith('Rules:'):
                # Add overrides at the end of the rules to make sure it is
                # overriden
                for line in f:
                    if not line.strip().startswith(f'{mod}|'):
                        mod_file_content += f'\t{mod}|{overrides_rel_path}\n'
                        mod_file_content += line
                        logging.info('Patching %s with custom overrides', mod_file_path)
                        break
                    mod_file_content += line
    return mod_file_content


def _prepare_instance(args, base_src_dir, map_paths):
    '''
    Fork the reference source with a modded strict configuration.
    We apparently can't do that without modifying the source, so we do that in
    every server instance.
    See https://github.com/OpenRA/OpenRA/wiki/Lock-server-settings
    '''

    server_data_dir = op.join(args.basewkdir, f'instance-{args.instance_id}')

    # Support dir: persists between run, as it contains the replays
    support_dir = op.join(server_data_dir, 'support_dir')
    if not op.exists(support_dir):
        os.makedirs(support_dir)

    # MOTD file
    if args.motd_file:
        with open(args.motd_file) as f:
            motd_content = f.read().format(id=args.instance_id)
        motd_path = op.join(support_dir, 'motd.txt')
        with open(motd_path, 'w') as f:
            f.write(motd_content)

    # Replace potential old instance sources with the reference ones
    src_dir = op.join(server_data_dir, 'src')
    logging.info('Bootstrap %s using %s', src_dir, base_src_dir)
    if op.exists(src_dir):
        shutil.rmtree(src_dir)
    shutil.copytree(base_src_dir, src_dir)

    # Create override file and reference it
    mod_dir = op.join(src_dir, 'mods', args.mod)
    overrides_rel_path = 'rules/server-overrides.yaml'
    overrides_path = op.join(mod_dir, overrides_rel_path)
    with open(overrides_path, 'w') as f:
        f.write(_overrides[args.mod])
    mod_file_path = op.join(mod_dir, 'mod.yaml')
    mod_file_content = _patched_rules(args.mod, mod_file_path, overrides_rel_path)
    with open(mod_file_path, 'w') as f:
        f.write(mod_file_content)

    # Sync restricted maps pack
    # We replace the maps in the sources instead of using the support directory
    # because we don't want the builtin maps to be available.
    mod_maps_dir = op.join(mod_dir, 'maps')
    shutil.rmtree(mod_maps_dir)
    os.makedirs(mod_maps_dir)
    for map_path in map_paths:
        logging.info('Copying %s to %s', map_path, mod_maps_dir)
        shutil.copy2(map_path, mod_maps_dir)

    return src_dir, support_dir


def _run_game_server(src_dir, mod, name, port, support_dir, password, bans_file):
    support_dir = op.abspath(support_dir)
    server_args = [
        'mono', '--debug', 'bin/OpenRA.Server.exe',
        'Engine.EngineDir=..',
        f'Game.Mod={mod}',
        f'Server.Name={name}',
        f'Server.ListenPort={port}',
        'Server.AdvertiseOnline=True',
        'Server.EnableSingleplayer=False',
        'Server.RequireAuthentication=True',
        'Server.EnableSyncReports=True',
        'Server.QueryMapRepository=False',
        'Server.Map=',
        'Server.RecordReplays=True',
        f'Engine.SupportDir={support_dir}',
    ]
    if password:
        server_args.append(f'Server.Password={password}')
    if bans_file:
        ban_str = ','.join(str(profile_id) for profile_id in get_profile_ids(bans_file))
        server_args.append(f'Server.ProfileIDBlacklist={ban_str}')
    logging.info('Spawning server with %s', server_args)
    os.chdir(src_dir)  # XXX: set PWD?
    subprocess.run(server_args)


def run():
    logging.basicConfig(level='INFO')
    parser = argparse.ArgumentParser()
    parser.add_argument('maps_file')
    parser.add_argument('--mod', default='ra')
    parser.add_argument('--motd-file')
    parser.add_argument('--instance-id', default=0, type=int)
    parser.add_argument('--label', default='Ladder Server {id}')
    parser.add_argument('--baseport', default=10100, type=int)
    parser.add_argument('--basewkdir', default='srvwrap')
    parser.add_argument('--version', default='release-20210321')
    parser.add_argument('--repo', default='https://github.com/OpenRA/OpenRA')
    parser.add_argument('--password')
    parser.add_argument('--bans-file')
    args = parser.parse_args()

    base_src_dir, map_paths = _setup_sources(args)
    instance_src_dir, support_dir = _prepare_instance(args, base_src_dir, map_paths)

    server_name = args.label.format(id=args.instance_id)
    server_port = args.baseport + args.instance_id
    _run_game_server(instance_src_dir, args.mod, server_name, server_port, support_dir, args.password, args.bans_file)
