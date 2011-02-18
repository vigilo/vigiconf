#!/bin/sh
################################################################################
# $Id$
# nagios.sh
# Copyright (C) 2007-2008 CS-SI
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
################################################################################

BASEDIR=$1
LOCATION=$2

if [ "$LOCATION" == "local" ] ; then
    if ! ls /etc/init.d/nagios >/dev/null 2>&1; then
        echo "Nagios is not installed"
        exit 1
    fi
fi

if [ -e /usr/sbin/nagios2 ]; then
    nver=2
elif [ -e /usr/sbin/nagios3 ]; then
    nver=3
elif [ -e /usr/sbin/nagios ]; then
    nver=""
else
    echo "Nagios not installed, aborting validation"
    exit 0
fi

if [ ! -d $BASEDIR/nagios ]; then
    echo "Nagios configuration is not available, aborting validation"
    exit 0
fi

# Création du fichier de configuration de test
testconffile=`mktemp /tmp/valid-nagios-XXXXXX`
trap "rm -f $testconffile" EXIT
chmod 644 $testconffile

# TODO: le chemin vers la conf de vigiconf est hardcodé ici

sed -e 's,/etc/vigilo/vigiconf/prod/nagios,'$BASEDIR'/nagios,' \
    /etc/nagios${nver}/nagios.cfg > $testconffile

# Utilisation de sudo pour pouvoir ecrire dans les repertoires specifiques de
# Nagios (/var/spool/nagios/)
sudo -n -u nagios /usr/sbin/nagios${nver} -v $testconffile
exit $?
