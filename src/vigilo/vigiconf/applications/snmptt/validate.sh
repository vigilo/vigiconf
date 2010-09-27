#!/bin/sh
if [ "$2" == "local" ] ; then
    ls /etc/init.d/snmptt >/dev/null || exit 1
fi
exit 0
