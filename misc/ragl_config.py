from datetime import date, timedelta

SEASON = 11
START_TIME = date(2021, 10, 11)
GROUP_STAGE_WEEKS = 7
PLAYOFF_WEEKS = 3
DURATION_WEEKS = GROUP_STAGE_WEEKS + PLAYOFF_WEEKS
END_TIME = START_TIME + timedelta(weeks=DURATION_WEEKS)
MAP_PACK_VERSION = '2021-10-18'
RELEASE = 'release-20210321'
RELEASE_URL = 'https://github.com/OpenRA/OpenRA/releases/tag/release-20210321'
SCHEDULE_URL = 'https://forum.openra.net/viewtopic.php?f=85&t=21511'
RULES_URL = 'https://forum.openra.net/viewtopic.php?f=85&t=21492'
PRIZE_POOL = '$1600'
DISCORD_URL = 'https://discord.gg/99zBDuS'
DISCORD_NAME = 'Red Alert Competitive Discord'

# We need <GAMES_PER_MATCH> done every <matchup_delay> (one matchup
# represents 2 games between the same players)
MATCHUP_DELAY = timedelta(weeks=1)
GAMES_PER_MATCH = 2


# Used by the Makefile to extract a value
if __name__ == '__main__':
    import sys
    print(globals()[sys.argv[1]])
