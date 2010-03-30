#!/usr/bin/env python
# -*- coding: utf-8 -*-
################################################################################
#
# ConfigMgr RRD StoreMe daemon configuration file generator
# Copyright (C) 2007 CS-SI
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

"""Generator for connector-metro, the RRD db generator

Ce générateur est implémenté avec les deux moteurs de templates
- Templator (spécifique vigilo)
- Genshi (fourni par TG)

La génération Genshi est activée au moyen d'une option dans settings.ini:
enable_genshi_generation = True

Pour éviter une double génération la génération Templator est
désactivée pour ce module en supprimant la classe de base Templator
"""

from __future__ import absolute_import

import os.path
import urllib

from .. import conf
from . import Templator 

# générateur désactivé
#class ConnectorMetroTpl(Templator):
class ConnectorMetroTpl:
    """Generator for connector-metro, the RRD db generator"""

    def generate(self):
        """Generate files"""
        templates = self.loadTemplates("connector-metro")
        #from pprint import pprint; pprint(templates)
        for (hostname, ventilation) in self.mapping.iteritems():
            if 'connector-metro' not in ventilation:
                continue
            h = conf.hostsConf[hostname]
            if not h.has_key("dataSources") or len(h['dataSources']) == 0:
                continue
            fileName = "%s/%s/connector-metro.conf.py" \
                       % (self.baseDir, ventilation['connector-metro'])
            if not os.path.exists(fileName):
                self.templateCreate(fileName, templates["header"],
                                    {"confid": conf.confid})
            self.templateAppend(fileName, templates["host"],
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
                rrdname = urllib.quote(k2).strip()
                tplvars["host"] = hostname
                tplvars["dsName"] = rrdname
                self.templateAppend(fileName, templates["ds"], tplvars)


from . import View

class ConnectorMetroView(View):
    """Generator for connector-metro, the RRD db generator
    
    Version utilisant le moteur de template genshi de TurboGears
    """
    
    def generate(self):
        """Generate files"""
        hosts = {}
        
        servers = self.get_hosts_by_server('connector-metro')
        
        for server, hosts in servers.iteritems():
            data_hosts = []
            
            for hostname in hosts:
                h = conf.hostsConf[hostname]
                if not h.has_key("dataSources") or len(h['dataSources']) == 0:
                    continue
                keys = h['dataSources'].keys()
                keys.sort()
                
                data_list = []
                
                for k2 in keys:
                    v2 = h['dataSources'][k2]
                    rrdname = urllib.quote(k2).strip()
                    data_list.append({
                             'type':v2['dsType'],
                             'name':rrdname, 'label':v2["label"]
                             })
                data_hosts.append({'hostname':hostname, 'data':data_list})
                
            self.render('connector-metro/connector-metro.conf',
                        {'hosts':data_hosts, 'confid':conf.confid},
                        "%s/connector-metro.conf.py" % server)
            
