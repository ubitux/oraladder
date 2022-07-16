class PlayoffOutcome:
    def __init__(self, p0, p1):
        self.profile_pair = (p0, p1)


def _extract_records(records, p0, p1, n):
    win_score = n // 2 + 1

    consumed = []
    p0_wins, p1_wins = 0, 0

    for record in records:
        if record.profile_pair == (p0, p1):
            p0_wins += 1
            consumed.append(record)
        elif record.profile_pair == (p1, p0):
            p1_wins += 1
            consumed.append(record)
        else:
            continue
        if win_score in (p0_wins, p1_wins):
            break

    for record in consumed:
        records.remove(record)  # will remove the first one only so this is fine

    return p0_wins, p1_wins


_STAR = '⭐'


def get_playoff2(n, players, records):
    '''best of N with 2 players'''

    p0, p1 = players
    p0_wins, p1_wins = _extract_records(records, p0, p1, n)
    win_score = n // 2 + 1
    if win_score in {p0_wins, p1_wins}:
        win_status = (_STAR, None) if p0_wins == win_score else (None, _STAR)
    else:
        win_status = (None, None)
    return [
        ('TieBreaker', win_status, (p0, p1), (p0_wins, p1_wins)),
    ]


_GOLD, _SILVER, _BRONZE = '🥇', '🥈', '🥉'


def get_playoff4(n, players, records):
    '''best of N with 4 players'''

    p0, p1, p2, p3 = players

    p0_wins, p3_wins = _extract_records(records, p0, p3, n)
    p1_wins, p2_wins = _extract_records(records, p1, p2, n)
    semi_wins = [p0_wins, p1_wins, p2_wins, p3_wins]
    semi_scores = dict(zip(players, semi_wins))

    matchups = [
        ('Semi-finals', (None, None), (p0, p3), (p0_wins, p3_wins)),
        ('Semi-finals', (None, None), (p1, p2), (p1_wins, p2_wins)),
    ]

    win_score = n // 2 + 1
    if semi_wins.count(win_score) != 2:
        return matchups

    fp0, fp1 = fp = {p for p, score in semi_scores.items() if score == win_score}
    bp0, bp1 = semi_scores.keys() - fp

    # Bronze
    bp0_wins, bp1_wins = _extract_records(records, bp0, bp1, n)
    bronze_scores = {bp0: bp0_wins, bp1: bp1_wins}
    if win_score in {bp0_wins, bp1_wins}:
        bronze_status = (_BRONZE, None) if bp0_wins == win_score else (None, _BRONZE)
    else:
        bronze_status = (None, None)
    matchups.append(('3rd Place', bronze_status, (bp0, bp1), (bp0_wins, bp1_wins)))

    # Finale
    fp0_wins, fp1_wins = _extract_records(records, fp0, fp1, n)
    finale_scores = {fp0: fp0_wins, fp1: fp1_wins}
    if win_score in {fp0_wins, fp1_wins}:
        finale_status = (_GOLD, _SILVER) if fp0_wins == win_score else (_SILVER, _GOLD)
    else:
        finale_status = (None, None)
    matchups.append(('Final', finale_status, (fp0, fp1), (fp0_wins, fp1_wins)))

    return matchups


def _run():
    god = 'goat'
    zxg = 'ZxGanon'
    mrk = 'Morkel'
    ilm = 'I Like Men'

    players2 = [ilm, zxg]
    players4 = [god, mrk, ilm, zxg]

    T = PlayoffOutcome
    records = (
        # fake tie breaker
        T(zxg, ilm), T(ilm, zxg), T(ilm, zxg),

        # finale
        T(god, zxg), T(god, zxg), T(god, zxg),
        T(zxg, ilm), T(ilm, zxg), T(ilm, zxg), T(zxg, ilm), T(ilm, zxg),
        T(god, mrk), T(mrk, god), T(mrk, god), T(god, mrk), T(god, mrk),
        T(ilm, mrk), T(mrk, ilm), T(mrk, ilm), T(ilm, mrk), T(mrk, ilm),
    )

    print(get_playoff2(3, players2, records))
    print(get_playoff4(5, players4, records))


if __name__ == '__main__':
    _run()
