#!/bin/sh
################################################################################
# $Id$
# perfdata.sh
# Copyright (C) 2007-2012 CS-SI
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

export BASE=$1

if [ ! -d $BASE/perfdata/ ]
then
    exit 0;
fi

ls -1 $BASE/perfdata/*.pm | sed -e 's,\(.*\),require "\1";,' > $BASE/perfdata.pm
echo "1;" >> $BASE/perfdata.pm
perl -e "require '$BASE/perfdata.pm'"
