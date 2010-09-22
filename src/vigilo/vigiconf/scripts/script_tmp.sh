#!/bin/bash

#Fichier de commandes externes de Nagios
NAGIOS_CMD_FILE='/var/nagios/rw/nagios.cmd'

# Get hostname and service
HOST=$1
SERV=$2
#Traduction du code de retour (equipement vers Nagios)
case $3 in
    1) CODE=3 ;;
    2|8) CODE=0 ;;
    3|5) CODE=1 ;;
    4|6|7) CODE=2 ;;
esac
#Descrition de la trap SNMP ('Status Information' dans l'interface Web de Nagios)
case $4 in
    str_1) INFORMATION="blablabla ${5}" ;;
    str_2) INFORMATION="blablabla ${5}" ;;
esac

#Recupere la date en secondes
DATE=`date +%s`
#Ajoute la ligne dans le fichier $NagiosCmdFile
/bin/echo "[$DATE] PROCESS_SERVICE_CHECK_RESULT;$HOST;$SERV;$CODE;
$INFORMATION" >> $NAGIOS_CMD_FILE

