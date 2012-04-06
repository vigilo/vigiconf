#!/bin/sh
# Copyright (C) 2011-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

sudo /etc/init.d/%(initname)s stop
for i in `seq 20`; do
    pgrep -u nagios %(nagios_bin)s >/dev/null || exit 0
    sleep 1
done

# On compte ici sur le fait que l'utilisateur "nagios"
# a des droits restreints et ne peut pas killer d'autres
# processus sans rapport avec Nagios.
sudo -u nagios pkill -KILL -u nagios %(nagios_bin)s
