#!/bin/sh

set -xeu

~/venv/bin/ora-ladder /home/ora/server-data-*/support_dir/Replays/
cp db.sqlite3 /home/web/venv/var/ladderweb-instance
