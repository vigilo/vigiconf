#!/bin/sh
# Copyright (C) 2007-2020 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

BASEDIR=$1

if [ "$2" = "local" ]; then
    if [ ! -e '%%(nagios_bin)s' ]; then
        echo "Nagios is not installed"
        exit 1
    fi
fi

if [ ! -e '%%(nagios_bin)s' ]; then
    echo "Nagios is not installed. Aborting validation."
    exit 0
fi

if [ ! -d "$BASEDIR/nagios" ]; then
    echo "Nagios configuration is not available. Aborting validation."
    exit 0
fi

# Création du fichier de configuration de test
testconffile=`mktemp /tmp/valid-nagios-XXXXXX`
trap "rm -f $testconffile" EXIT
chmod 644 $testconffile

# Normalisation de targetconfdir : on remplace les successions
# de "/" par un seul "/" et on supprime l'éventuel "/" final.
TARGETCONFDIR=`echo '%%(targetconfdir)s' | sed -e 's,/\+,/,g;s,/$,,'`
# On substitue le chemin jusqu'à l'arborescence de la configuration de Vigilo
# de production par le chemin jusqu'à l'arborescence de validation.
sed -e 's,'$TARGETCONFDIR'/prod/nagios,'$BASEDIR'/nagios,' '%%(nagios_cfg)s' > $testconffile

# Utilisation de sudo pour pouvoir ecrire dans les repertoires specifiques de
# Nagios (/var/spool/nagios/)
# Sudo en root plutôt qu'en 'nagios' parce que certaines distribs ne laissent
# le droit d'exécution de Nagios qu'à root (mdv2010+)
sudo '%%(nagios_bin)s' -v $testconffile
exit $?
