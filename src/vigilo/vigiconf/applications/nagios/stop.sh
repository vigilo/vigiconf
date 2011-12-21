#!/bin/sh

sudo /etc/init.d/%(initname)s stop
for i in `seq 20`; do
    pgrep %(nagios_bin)s >/dev/null || exit 0
    sleep 1
done

# On compte ici sur le fait que l'utilisateur "nagios"
# a des droits restreints et ne peut pas killer d'autres
# processus sans rapport avec Nagios.
sudo -u nagios pkill -u nagios -KILL %(nagios_bin)s
