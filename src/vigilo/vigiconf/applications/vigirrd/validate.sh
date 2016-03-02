#!/bin/sh
# Copyright (C) 2007-2016 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

if [ "$2" == "local" ]; then
    if [ ! -e '%%(httpd_init)s' ]; then
        exit 1
    fi
fi

export BASE="$1"

if [ ! -r "$BASE/vigirrd.db" ]; then
    exit 0
fi

'%%(sqlite3_bin)s' "$BASE/vigirrd.db" "SELECT COUNT(*) FROM perfdatasource" && \
'%%(sqlite3_bin)s' "$BASE/vigirrd.db" "SELECT COUNT(*) FROM host" && \
'%%(sqlite3_bin)s' "$BASE/vigirrd.db" "SELECT COUNT(*) FROM graph" && \
'%%(sqlite3_bin)s' "$BASE/vigirrd.db" "SELECT COUNT(*) FROM graphperfdatasource"
exit $?
