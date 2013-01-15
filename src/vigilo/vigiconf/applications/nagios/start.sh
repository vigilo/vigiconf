#!/bin/sh
# Copyright (C) 2011-2013 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

confdir="$1"

if [ ! -f "$confdir/nagios/nagios.cfg" ]; then
    echo "No Nagios configuration file, not starting Nagios"
    exit 0
fi
sudo '%%(nagios_init)s' start
