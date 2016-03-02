#!/bin/sh
# Copyright (C) 2007-2016 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

export BASE=$1

if [ "$2" == "local" ]; then
    if [ ! -e '%%(metro_init)s' ]; then
        exit 1
    fi
fi

if [ ! -r "$BASE/connector-metro.db" ]; then
    exit 0
fi

'%%(sqlite3_bin)s' "$BASE/connector-metro.db" "SELECT COUNT(*) FROM perfdatasource" && \
'%%(sqlite3_bin)s' "$BASE/connector-metro.db" "SELECT COUNT(*) FROM rra" && \
'%%(sqlite3_bin)s' "$BASE/connector-metro.db" "SELECT COUNT(*) FROM pdsrra"
exit $?
