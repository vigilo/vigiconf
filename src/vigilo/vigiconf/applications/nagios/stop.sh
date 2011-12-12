#!/bin/sh

sudo /etc/init.d/%(initname)s stop
for i in `seq 20`; do
    pgrep %(nagios_bin)s >/dev/null || exit 0
    sleep 1
done

# On tente de déterminer l'emplacement du fichier de PID de Nagios
# à partir des emplacements les plus probables pour le fichier nagios.cfg.
nagios_pidfile=
for d in /etc/nagios3 /etc/nagios; do
    if test -f "$d/nagios.cfg"; then
        possible_pidfile=`egrep "^[[:space:]]*lock_file" "$d/nagios.cfg"|cut -d= -f2`
        # Élimine les espaces éventuels autour du chemin.
        possible_pidfile=`echo $possible_pidfile`
        if test -f $possible_pidfile; then
            nagios_pidfile=$possible_pidfile
            break
        fi
    fi
done

# Si Nagios n'a pas réussi à terminer correctement
# avec la manière douce, on tente la manière forte.
nagios_pid=`head -n 1 $nagios_pidfile 2> /dev/null`

# Pas de (fichier de) PID, on ne fait rien
# (Nagios s'est probablement arrêté correctement entre temps).
if test -z "$nagios_pid"; then
    exit 0
fi
sudo -u nagios kill -KILL -- -$nagios_pid 2>/dev/null || :
