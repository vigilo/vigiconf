# -*- coding: utf-8 -*-
################################################################################
#
# VigiConf
# Copyright (C) 2007-2011 CS-SI
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

"""
Generator for connector-metro, the RRD db generator
"""


import os.path
import urllib

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib.generators import FileGenerator


class ConnectorMetroGen(FileGenerator):
    """Generator for connector-metro, the RRD db generator"""

    def generate(self):
        """Generate files"""
        for (hostname, ventilation) in self.mapping.iteritems():
            if 'connector-metro' not in ventilation:
                continue
            h = conf.hostsConf[hostname]
            if not h.has_key("dataSources") or len(h['dataSources']) == 0:
                continue
            fileName = "%s/%s/connector-metro.conf.py" \
                       % (self.baseDir, ventilation['connector-metro'])
            if not os.path.exists(fileName):
                self.templateCreate(fileName, self.templates["header"],
                                    {"confid": conf.confid})
            self.templateAppend(fileName, self.templates["host"],
                                {'host': hostname})
            keys = h['dataSources'].keys()
            keys.sort()
            for k2 in keys:
                v2 = h['dataSources'][k2]
                tplvars = {
                    'host': hostname,
                    'dsType': v2['dsType'],
                    'dsName': k2,
                    'label': v2["label"],
                }
                rrdname = urllib.quote_plus(k2).strip()
                tplvars["host"] = hostname
                tplvars["dsName"] = rrdname
                self.templateAppend(fileName, self.templates["ds"], tplvars)

