################################################################################
#
# ConfigMgr CorrTrap configuration file generator
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

"""Generator for the SNMP trap collector (CorrTrap)"""

import os
import os.path

import conf
from generators import Templator 

class CorrTrapTpl(Templator):
    """Generator for the SNMP trap collector (CorrTrap)"""
            
    def generate(self):
        """Generate files"""
        templates = self.loadTemplates("corrtrap")
        data = {}
        serverList = [] 
        corrsup_server = None
        
        for (host, ventilation) in self.mapping.iteritems():            
            if 'corrtrap' in ventilation:
                h = conf.hostsConf[host]
                server = ventilation['corrtrap']
                corrsup_server = ventilation['corrsup']
                if not (data.has_key(server)):
                    data[server] = {}
                    serverList.append(server)
        
                for (service, ip) in h['trapItems'].iteritems():
                    for (key, value) in ip.iteritems():
                        if not (data[server].has_key(service)): 
                            data[server][service] = {key: value}
                        else:
                            if not (data[server][service].has_key(key)): 
                                data[server][service][key] = value
                            else:
                                self.addWarning("corrtrap",
                                                "corrTrap duplicate key : " 
                                               +"[%s][%s][%s]"
                                               % (server, service, key))
        
        for server in serverList:
            dirName = "%s/%s/corrtrap" % (self.baseDir, server)
            for i in ('rules.sec', ):
                self.copyFile("%s/corrtrap/%s" % (conf.templatesDir, i),
                              "%s/%s" % (dirName, i))
    
            if not os.path.exists("%s/mapTrap.pm" % (dirName)):
                fileName = "%s/mapTrap.pm" % (dirName)                    
                self.templateCreate(fileName, templates["header"],
                                    {"confid": conf.confid,
                                     "corrsup": corrsup_server})
    
                self.templateAppend(fileName, "\nmy %%mapTrap=(\n", ())
                for (key, value) in data[server].iteritems():
                    self.templateAppend(fileName, "\t\"%s\" => {\n", (key))
                    for (key2, value2) in value.iteritems():
                        self.templateAppend(fileName,
                                            "\t\t\"%s\" => \"%s\",\n",
                                            (key2, value2))
                    self.templateAppend(fileName, "\t},\n", ())

                self.templateAppend(fileName, ");\n", ())
                    
                self.templateAppend(fileName, templates["footer"],
                                    {"mapTrap": "%mapTrap"})


# vim:set expandtab tabstop=4 shiftwidth=4:
