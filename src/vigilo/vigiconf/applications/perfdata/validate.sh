#!/bin/sh
# Copyright (C) 2007-2019 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

export BASE=$1

if [ ! -d "$BASE/perfdata/" ]
then
    exit 0;
fi

find "$BASE/perfdata/" -name '*.pm' -printf 'require "%%%%p";\n' > "$BASE/perfdata.pm"
printf '1;\n' >> "$BASE/perfdata.pm"
perl -e "require '$BASE/perfdata.pm'"
