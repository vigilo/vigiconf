#!/bin/sh
# Copyright (C) 2007-2019 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

export BASE=$1

if [ "$2" == "local" ]; then
    which vigilo-connector-metro 2> /dev/null >&2
    if [ $? -ne 0 ]; then
        echo "vigilo-connector-metro n'est pas installé sur la machine"
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
