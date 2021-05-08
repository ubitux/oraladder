#!/bin/sh

set -xeu

~/venv/bin/ora-ladder --bans-file /home/ora/bans.list -d db-ra-all.sqlite3      /home/ora/srv-ladder/instance-*/support_dir/Replays/
~/venv/bin/ora-ladder --bans-file /home/ora/bans.list -d db-ra-2m.sqlite3 -p 2m /home/ora/srv-ladder/instance-*/support_dir/Replays/
~/venv/bin/ora-ladder --bans-file /home/ora/bans.list -d db-td-all.sqlite3      /home/ora/srv-ladder-td/instance-*/support_dir/Replays/
~/venv/bin/ora-ladder --bans-file /home/ora/bans.list -d db-td-2m.sqlite3 -p 2m /home/ora/srv-ladder-td/instance-*/support_dir/Replays/
~/venv/bin/ora-ragl   -d db-ragl.sqlite3   /home/ora/srv-ragl/instance-*/support_dir/Replays/

cp -v db-ragl.sqlite3 /home/web/venv/var/raglweb-instance/
cp -v db-*-*.sqlite3  /home/web/venv/var/ladderweb-instance/
