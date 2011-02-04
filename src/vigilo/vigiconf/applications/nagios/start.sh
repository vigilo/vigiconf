#!/bin/sh

confdir="$1"

conffiles="`ls $confdir/nagios/*.cfg 2>/dev/null`"
if [ -z "$conffiles" ]; then
    echo "No Nagios configuration file, not starting Nagios"
fi
sudo /etc/init.d/%(initname)s start

