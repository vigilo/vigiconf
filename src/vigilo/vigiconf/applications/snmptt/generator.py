###############################################################################
#
# ConfigMgr snmpTT configuration file generator
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
###############################################################################

"""Generator for the SNMP trap collector (snmpTT)"""

import os
import os.path
import re

from vigilo.common.conf import settings

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib.generators import FileGenerator

class SnmpTTGen(FileGenerator):
    """Generator for the SNMP trap collector (snmpTT)"""

    def generate(self):
        super(SnmpTTGen, self).generate()

    def generate_host(self, hostname, vserver):
        h = conf.hostsConf[hostname]
        # loads the configuration for host
        h = conf.hostsConf[hostname]
        if not len(h["snmpTrap"]): # if no trap is configured.
            return

        fileName = os.path.join(self.baseDir, vserver,
                                     "snmptt", "snmptt.conf")
        fileName_nagios = os.path.join(self.baseDir, vserver,
                                     "nagios", "nagios_trap.cfg")

        match = "MATCH $ar: %s"
        # we received something like
        # {servicename1: {OID:{label:<>,command:<>, address:<>, etc.}, OID: {..}},
        #  servicename2: etc.
        for srvname in h["snmpTrap"].keys():
            if srvname not in h["services"].keys():
                self.templateCreate(fileName_nagios, self.templates["nagios_trap"],
                    {
                        "hostname": hostname,
                        "servicename": srvname,
                    }
                )
            for oid in h["snmpTrap"][srvname].keys():
                vals = h["snmpTrap"][srvname][oid]
                if not os.path.exists(fileName):
                    templateFunct = self.templateCreate
                else:
                    templateFunct = self.templateAppend
                # from snmptt website: If no MATCH MODE= line exists, it defaults to 'or'.
                if isinstance(vals["address"], list):
                    all_match = "\n".join(match % i for i in vals["address"])
                    all_match+= "\nMATCH MODE:%s" % vals["mode"]
                else:
                    all_match = match % vals["address"]

                templateFunct(fileName, self.templates["snmptt.conf"],
                    {"event": vals["label"],
                        "oid": oid,
                        "command": vals["command"],
                        "host": hostname,
                        "service": srvname,
                        "match" : all_match
                        })

# vim:set expandtab tabstop=4 shiftwidth=4:
