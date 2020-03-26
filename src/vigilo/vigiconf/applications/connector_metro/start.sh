#!/bin/sh
# Copyright (C) 2020 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

set -e

for svc in %%(metro_svc)s; do
    sudo service "$svc" restart
done
