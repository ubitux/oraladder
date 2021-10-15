from datetime import date, timedelta

SEASON = 11
START_TIME = date(2021, 10, 11)
MAP_PACK_VERSION = "2021-10-09"
RELEASE = 'release-20210321'
RELEASE_URL = 'https://github.com/OpenRA/OpenRA/releases/tag/release-20210321'
SCHEDULE_URL = 'https://forum.openra.net/viewtopic.php?f=85&t=21511'
PRIZE_POOL = '$1600'
STAFF = ('.won (.1)', 'Happy', 'Anjew')
DISCORD_URL = 'https://discord.gg/99zBDuS'
DISCORD_NAME = 'Red Alert Competitive Discord'
CONTACT_MAIL = 'OpenRA.RAGL@gmail.com'

# We need <matchup_count> done every <matchup_delay> (one matchup
# represents 2 games between the same players)
MATCHUP_DELAY = timedelta(weeks=1)
MATCHUP_COUNT = 2


# Used by the Makefile to extract a value
if __name__ == '__main__':
    import sys
    print(globals()[sys.argv[1]])
