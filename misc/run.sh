#!/bin/sh

if [ $# -ne 1 ]; then
    echo "Usage: $0 <ID>"
    exit 0
fi

set -xeu
n=$1


#
# User configuration
#

mod=ra
version=playtest-20201213
name="|oraladder.net| Competitive 1v1 Ladder Server $n"


#
# Base configuration
#

port=$((10100+$n))
basedir=$(cd $(dirname $0) && pwd -P)
server_data=$basedir/server-data-$n
support_dir=$server_data/support_dir
src_dir=$server_data/src


#
# Make sure the reference sources are in the appropriate version and compiled
#

ref_srcdir=$basedir/OpenRA
if [ ! -d $ref_srcdir ]; then
    git clone https://github.com/OpenRA/OpenRA/ $ref_srcdir
fi
(
    cd $ref_srcdir
    cur_version=$(cat VERSION)
    if [ $cur_version != $version ]; then
        git reset --hard
        git clean -fdx
        git checkout $version
        make version VERSION=$version
        # Using Server.Map="" doesn't work for selecting a random map because it will
        # filter only maps in the "Conquest" category (RAGL maps typically aren't), so
        # we use this workaround instead for now
        sed '/"Conquest"/{N;d}' -i OpenRA.Game/Map/MapCache.cs
        make
    fi
)


#
# MOTD
#

mkdir -p $support_dir
cat <<EOF > $support_dir/motd.txt
Welcome to the competitive 1v1 ladder server $n

This server is linked to oraladder.net. The next game played here will be
recorded and made available publicly, and the ranking of the players updated
accordingly.
EOF


#
# Fork the reference source with a modded strict configuration.
# We apparently can't do that without modifying the source, so we do that in
# every server instance.
# See https://github.com/OpenRA/OpenRA/wiki/Lock-server-settings
#

rsync -av --delete $ref_srcdir/ $src_dir
overrides=rules/server-overrides.yaml
sed '/^Rules:$/a \\tra|'$overrides -i $src_dir/mods/$mod/mod.yaml
cat <<EOF > $src_dir/mods/$mod/$overrides
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
EOF


#
# Sync restricted maps pack
# We replace the maps in the sources instead of using the support directory
# because we don't want the builtin maps to be available.
#

maps_dst_dir=$src_dir/mods/$mod/maps
mkdir -p $maps_dst_dir
rsync -av --delete $basedir/maps/ $maps_dst_dir


#
# Run the game server
#

cd $src_dir
while true; do
    mono --debug bin/OpenRA.Server.exe                         \
        Engine.EngineDir=".."                                  \
        Game.Mod=$mod                                          \
        Server.Name="$name"                                    \
        Server.ListenPort=$port                                \
        Server.AdvertiseOnline=True                            \
        Server.EnableSingleplayer=False                        \
        Server.RequireAuthentication=True                      \
        Server.EnableSyncReports=True                          \
        Server.QueryMapRepository=False                        \
        Server.Map=""                                          \
        Server.RecordReplays=True                              \
        Engine.SupportDir="$support_dir"
done
