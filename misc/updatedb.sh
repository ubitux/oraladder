#!/bin/sh

set -xeu

~/venv/bin/ora-ladder -d db-ladder.sqlite3 /home/ora/srv-ladder/instance-*/support_dir/Replays/
~/venv/bin/ora-ladder -d db-ladder-2m.sqlite3 -p 2m /home/ora/srv-ladder/instance-*/support_dir/Replays/
~/venv/bin/ora-ragl   -d db-ragl.sqlite3   /home/ora/srv-ragl/instance-*/support_dir/Replays/

cp db-ladder.sqlite3 /home/web/venv/var/ladderweb-instance/db.sqlite3
cp db-ladder-2m.sqlite3 /home/web/venv/var/ladderweb-instance/db-2m.sqlite3
cp db-ragl.sqlite3   /home/web/venv/var/raglweb-instance/db-ragl.sqlite3
