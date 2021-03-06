#!/bin/sh
# Copyright (C) 2011-2020 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

sudo service '%%(nagios_svc)s' stop
for i in `seq 20`; do
    pgrep -u %%(nagios_user)s '%%(nagios_bin)s' >/dev/null || exit 0
    sleep 1
done

# On compte ici sur le fait que l'utilisateur "nagios"
# a des droits restreints et ne peut pas killer d'autres
# processus sans rapport avec Nagios.
sudo -u %%(nagios_user)s pkill -KILL -u %%(nagios_user)s '%%(nagios_bin)s'
