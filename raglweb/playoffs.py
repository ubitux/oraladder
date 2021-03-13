class PlayoffOutcome:
    def __init__(self, p0, p1):
        self.profile_pair = (p0, p1)


def records_count(records, outcome):
    return len([r for r in records if outcome == r.profile_pair])


def get_playoff2(n, players, records):
    '''best of N with 2 players'''

    p0, p1 = players
    scores = {
        p0: records_count(records, (p0, p1)),
        p1: records_count(records, (p1, p0)),
    }
    return [
        ('TieBreaker', (None, None), (p0, p1), (scores[p0], scores[p1])),
    ]


_GOLD, _SILVER, _BRONZE = '🥇', '🥈', '🥉'


def get_playoff4(n, players, records):
    '''best of N with 4 players'''

    p0, p1, p2, p3 = players

    semi_scores = {
        p0: records_count(records, (p0, p3)),
        p3: records_count(records, (p3, p0)),
        p1: records_count(records, (p1, p2)),
        p2: records_count(records, (p2, p1)),
    }

    matchups = [
        ('Semi-finals', (None, None), (p0, p3), (semi_scores[p0], semi_scores[p3])),
        ('Semi-finals', (None, None), (p1, p2), (semi_scores[p1], semi_scores[p2])),
    ]

    win_score = n // 2 + 1
    if list(semi_scores.values()).count(win_score) != 2:
        return matchups

    fp0, fp1 = fp = {p for p, score in semi_scores.items() if score == win_score}
    bp0, bp1 = semi_scores.keys() - fp

    # Bronze
    bronze_scores = {
        bp0: records_count(records, (bp0, bp1)),
        bp1: records_count(records, (bp1, bp0)),
    }
    if win_score in bronze_scores.values():
        bronze_status = (_BRONZE, None) if bronze_scores[bp0] == win_score else (None, _BRONZE)
    else:
        bronze_status = (None, None)
    matchups.append(('3rd Place', bronze_status, (bp0, bp1), (bronze_scores[bp0], bronze_scores[bp1])))

    # Finale
    finale_scores = {
        fp0: records_count(records, (fp0, fp1)),
        fp1: records_count(records, (fp1, fp0)),
    }
    if win_score in finale_scores.values():
        finale_status = (_GOLD, _SILVER) if finale_scores[fp0] == win_score else (_SILVER, _GOLD)
    else:
        finale_status = (None, None)
    matchups.append(('Final', finale_status, (fp0, fp1), (finale_scores[fp0], finale_scores[fp1])))

    return matchups


def _run():
    god = 'goat'
    zxg = 'ZxGanon'
    mrk = 'Morkel'
    ilm = 'I Like Men'

    players = [god, mrk, ilm, zxg]

    T = PlayoffOutcome
    records = (
        T(god, zxg), T(god, zxg), T(god, zxg),
        T(zxg, ilm), T(ilm, zxg), T(ilm, zxg), T(zxg, ilm), T(ilm, zxg),
        T(god, mrk), T(mrk, god), T(mrk, god), T(god, mrk), T(god, mrk),
        T(ilm, mrk), T(mrk, ilm), T(mrk, ilm), T(ilm, mrk), T(mrk, ilm),
    )

    print(get_playoff4(5, players, records))

if __name__ == '__main__':
    _run()
