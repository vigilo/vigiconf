#!/bin/sh
# Copyright (C) 2011-2020 CS GROUP – France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

confdir="$1"

if [ ! -f "$confdir/nagios/nagios.cfg" ]; then
    echo "No Nagios configuration file, not starting Nagios"
    exit 0
fi
sudo service '%%(nagios_svc)s' start
