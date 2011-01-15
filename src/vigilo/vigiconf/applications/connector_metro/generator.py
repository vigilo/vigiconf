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

    def generate_host(self, hostname, vserver):
        """Generate files"""
        h = conf.hostsConf[hostname]
        if "dataSources" not in h or not h['dataSources']:
            return
        fileName = os.path.join(self.baseDir, vserver, "connector-metro.conf.py")
        if not os.path.exists(fileName):
            self.templateCreate(fileName, self.templates["header"],
                                {"confid": conf.confid})
        self.templateAppend(fileName, self.templates["host"],
                            {'host': hostname})
        keys = h['dataSources'].keys()
        keys.sort()
        netflow_keys = []
        for ip in h['netflow'].get('IPs', {}):
            netflow_keys.append("in_bytes_" + ip)
            netflow_keys.append("out_bytes_" + ip)
            netflow_keys.append("in_packets_" + ip)
            netflow_keys.append("out_packets_" + ip)
        for k2 in keys:
            v2 = h['dataSources'][k2]
            if k2 in netflow_keys:
                k2 = "/".join(i for i in k2.split("/")[:-1])
            tplvars = {
                'host': hostname,
                'dsType': v2['dsType'],
                'dsName': k2,
                'label': v2["label"],
            }
            if "max" in v2 and v2["max"] is not None:
                # toute valeur supérieure collectée sera ignorée
                tplvars["max"] = float(v2["max"]) * 100 # marge de sécurité
            else:
                tplvars["max"] = "U"
            if "min" in v2 and v2["min"] is not None:
                # toute valeur inférieure collectée sera ignorée
                tplvars["min"] = float(v2["min"])
            else:
                tplvars["min"] = "U"
            if not k2 in netflow_keys:
                self.templateAppend(fileName, self.templates["ds"], tplvars)
            else:
                self.templateAppend(fileName, self.templates["ds_netflow"], tplvars)


