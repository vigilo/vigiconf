#!/bin/sh
# Copyright (C) 2007-2018 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

export BASE=$1

if [ ! -d "$BASE/collector/" ]
then
    exit 0;
fi

find "$BASE/collector/" -name '*.pm' -printf 'require "%%%%p";\n' > "$BASE/collector.pm"
printf '1;\n' >> "$BASE/collector.pm"
perl -e "require '$BASE/collector.pm'"
