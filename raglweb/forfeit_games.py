from datetime import datetime
from sqlite3 import Connection


def get_forfeit_win_loss_stats(db: Connection) -> dict:
    query = """
    SELECT pl.profile_id, pl.profile_name, 
        (SELECT COUNT(*) FROM forfeit_games fg where fg.profile_id0=pl.profile_id) as wins, 
        (SELECT COUNT(*) FROM forfeit_games fg where fg.profile_id1=pl.profile_id) as losses 
        FROM players pl
    """
    res = db.execute(query).fetchall()
    stats = {}
    for row in res:
        stats[row[0]] = {
            "id": row[0],
            "name": row[1],
            "wins": row[2],
            "losses": row[3],
        }
    return stats


def get_player_forfeit_games(db: Connection, player_id: int) -> dict:
    query = f"SELECT fg.profile_id0, (SELECT profile_name FROM players WHERE profile_id=fg.profile_id0) as p0_name, " \
            f"fg.profile_id1, (SELECT profile_name FROM players WHERE profile_id=fg.profile_id1) as p1_name, " \
            f"fg.decision_timestamp as end_time, fg.reason " \
            f"FROM forfeit_games fg " \
            f"WHERE profile_id0='{player_id}' OR profile_id1={player_id}"
    res = db.execute(query).fetchall()
    records = {}
    for row in res:
        opponent_id = row[0] if row[0] != player_id else row[2]
        opponent_name = row[1] if row[0] != player_id else row[3]
        game = {
            'opponent': opponent_name,
            'opponent_id': opponent_id,
            'date': datetime.fromisoformat(row[4]).strftime('%Y-%m-%d'),
            'map': row[5],
            'outcome': 'Won' if row[0] == player_id else 'Lost',
            'hash': ""
        }
        if opponent_id in records.keys():
            records[opponent_id].append(game)
        else:
            records[opponent_id] = [game]

    return records
