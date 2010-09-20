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

from vigilo.common.conf import settings

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib.generators import FileGenerator

class CorrTrapGen(FileGenerator):
    """Generator for the SNMP trap collector (CorrTrap)"""

    def generate(self):
        """Generate files"""
        data = {}
        serverList = []

        for (host, ventilation) in self.mapping.iteritems():
            if 'corrtrap' in ventilation:
                h = conf.hostsConf[host]
                server = ventilation['corrtrap']
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
            self.copy("rules.sec", os.path.join(dirName, "rules.sec"))
            #for t in ('rules.sec', ):
                #dest = open(os.path.join(dirName, t), 'w')
                #dest.write(self.templates[t])
                #dest.close()

            if not os.path.exists("%s/mapTrap.pm" % (dirName)):
                fileName = "%s/mapTrap.pm" % (dirName)
                self.templateCreate(fileName, self.templates["header"],
                                    {"confid": conf.confid,
                                     "socket": settings["vigiconf"].get(
                                                    "socket_nagios_to_vigilo"
                                                    ),
                                    })

                self.templateAppend(fileName, "\nmy %%mapTrap=(\n", ())
                for (key, value) in data[server].iteritems():
                    self.templateAppend(fileName, "\t\"%s\" => {\n", (key))
                    for (key2, value2) in value.iteritems():
                        self.templateAppend(fileName,
                                            "\t\t\"%s\" => \"%s\",\n",
                                            (key2, value2))
                    self.templateAppend(fileName, "\t},\n", ())

                self.templateAppend(fileName, ");\n", ())

                self.templateAppend(fileName, self.templates["footer"],
                                    {"mapTrap": "%mapTrap"})


# vim:set expandtab tabstop=4 shiftwidth=4:
