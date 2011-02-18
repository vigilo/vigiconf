#!/bin/sh

sudo -n /etc/init.d/%(initname)s stop
while i in `seq 30`; do
    pgrep nagios >/dev/null || break
    sleep 1
done

