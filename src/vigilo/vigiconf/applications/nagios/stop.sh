#!/bin/sh

sudo /etc/init.d/%(initname)s stop
for i in `seq 20`; do
    pgrep %(nagios_bin)s >/dev/null || exit 0
    sleep 1
done
sudo -u nagios pkill -9 %(nagios_bin)s

