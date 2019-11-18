CREATE TABLE IF NOT EXISTS accounts (
	fingerprint  TEXT PRIMARY KEY,
	profile_id   INTEGER NOT NULL,
	profile_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS players (
	profile_id   INTEGER PRIMARY KEY,
	profile_name TEXT NOT NULL,
	wins         INTEGER NOT NULL,
	losses       INTEGER NOT NULL,
	prv_rating   INTEGER NOT NULL,
	rating       INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS outcomes (
	start_time            TEXT NOT NULL,
	end_time              TEXT NOT NULL,
	filename              TEXT NOT NULL,
	profile_id0           TEXT NOT NULL,
	profile_id1           TEXT NOT NULL,
	rating_0_prv          INTEGER NOT NULL,
	rating_1_prv          INTEGER NOT NULL,
	rating_0              INTEGER NOT NULL,
	rating_1              INTEGER NOT NULL,
	faction_0             TEXT NOT NULL,
	faction_1             TEXT NOT NULL,
	selected_faction_0    TEXT NOT NULL,
	selected_faction_1    TEXT NOT NULL,
	map_uid               TEXT NOT NULL,
	map_title             TEXT NOT NULL,
	UNIQUE(start_time, end_time, filename, profile_id0, profile_id1)
);
