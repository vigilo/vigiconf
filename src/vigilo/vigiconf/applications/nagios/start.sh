#!/bin/sh
# Copyright (C) 2011-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

confdir="$1"

conffiles="`ls $confdir/nagios/*.cfg 2>/dev/null`"
if [ -z "$conffiles" ]; then
    echo "No Nagios configuration file, not starting Nagios"
    exit 0
fi
sudo /etc/init.d/%(initname)s start

