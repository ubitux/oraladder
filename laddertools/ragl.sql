CREATE TABLE IF NOT EXISTS accounts (
	fingerprint  TEXT PRIMARY KEY,
	profile_id   INTEGER NOT NULL,
	profile_name TEXT NOT NULL,
	avatar_url   TEXT
);

CREATE TABLE IF NOT EXISTS players (
	profile_id   INTEGER PRIMARY KEY,
	profile_name TEXT NOT NULL,
	avatar_url   TEXT NOT NULL,
	wins         INTEGER NOT NULL,
	losses       INTEGER NOT NULL,
	division     TEXT NOT NULL,
	status       TEXT
);

CREATE TABLE IF NOT EXISTS outcomes (
	hash                  TEXT NOT NULL PRIMARY KEY,
	start_time            TEXT NOT NULL,
	end_time              TEXT NOT NULL,
	filename              TEXT NOT NULL,
	profile_id0           INTEGER NOT NULL,
	profile_id1           INTEGER NOT NULL,
	faction_0             TEXT NOT NULL,
	faction_1             TEXT NOT NULL,
	selected_faction_0    TEXT NOT NULL,
	selected_faction_1    TEXT NOT NULL,
	map_uid               TEXT NOT NULL,
	map_title             TEXT NOT NULL
);

-- "CREATE TABLE playoff_outcomes LIKE outcomes;"
-- is not supported with SQLite so we dup the layout
-- XXX: use a bool flag field instead?
CREATE TABLE IF NOT EXISTS playoff_outcomes (
	hash                  TEXT NOT NULL PRIMARY KEY,
	start_time            TEXT NOT NULL,
	end_time              TEXT NOT NULL,
	filename              TEXT NOT NULL,
	profile_id0           INTEGER NOT NULL,
	profile_id1           INTEGER NOT NULL,
	faction_0             TEXT NOT NULL,
	faction_1             TEXT NOT NULL,
	selected_faction_0    TEXT NOT NULL,
	selected_faction_1    TEXT NOT NULL,
	map_uid               TEXT NOT NULL,
	map_title             TEXT NOT NULL
);

CREATE TABLE playoff_playersets (
	playoff_id  TEXT NOT NULL,
	profile_id  INTEGER NOT NULL
);

CREATE TABLE playoffs (
	label   TEXT NOT NULL PRIMARY KEY,
	bestof  INTEGER NOT NULL
);

CREATE TABLE forfeit_games (
	profile_id0           INTEGER NOT NULL,
	profile_id1           INTEGER NOT NULL,
	decision_timestamp    TEXT NOT NULL,
	reason                TEXT DEFAULT NULL
)