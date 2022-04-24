from datetime import date, timedelta

SEASON = 12
START_TIME = date(2022, 4, 25)
GROUP_STAGE_WEEKS = 7
PLAYOFF_WEEKS = 3
DURATION_WEEKS = GROUP_STAGE_WEEKS + PLAYOFF_WEEKS
END_TIME = START_TIME + timedelta(weeks=DURATION_WEEKS)
MAP_PACK_VERSION = '2022-04-20'
RELEASE = 'release-20210321'
RELEASE_URL = 'https://github.com/OpenRA/OpenRA/releases/tag/release-20210321'
SCHEDULE_URL = 'https://forum.openra.net/viewtopic.php?f=85&t=21599'
RULES_URL = 'https://forum.openra.net/viewtopic.php?f=85&t=21590'
PRIZE_POOL = '$???'
DISCORD_URL = 'https://discord.gg/99zBDuS'
DISCORD_NAME = 'Red Alert Competitive Discord'
GAMES_PER_MATCH = 2


# Used by the Makefile to extract a value
if __name__ == '__main__':
    import sys
    print(globals()[sys.argv[1]])
