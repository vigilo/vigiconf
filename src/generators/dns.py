################################################################################
#
# ConfigMgr DNS Zone configuration file generator
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

"""Generator for the DNS"""

import os
import time

import conf
from generators import Templator 

class DnsTpl(Templator):
    """Generator for the DNS"""

    def getForwardName(self, hostname):
        """
        Checks that the hostname is in an allowed dns zone.
        Splits the hostname into an hostname+domain part and a dns zone
        """
        for i in conf.dns['allowedDNSZones']:
            if hostname.endswith("." + i):
                return (hostname.replace("." + i, ""), i)
        return None

    def getReverseName(self, ip):
        """
        Checks that the ip address is in an allowed dns zone.
        Splits the ip into an entry part and a dns zone
        """
        for i in conf.dns['allowedIPBases']:
            if ip.startswith(i + "."):
                z = i.split(".")
                z.reverse()
                n = ip.replace(i + ".", "").split(".")
                n.reverse()
                return (".".join(n), ".".join(z))
        return None

    def generate(self):
        """Generate files"""
        templates = self.loadTemplates("dns")
        for (hostname, ventilation) in self.mapping.iteritems():
            servers = []
            if 'dns1' in ventilation:
                servers.append(ventilation["dns1"])
            if 'dns2' in ventilation:
                servers.append(ventilation["dns2"])
            for server in servers:
                h = conf.hostsConf[hostname]
                tplval = {"fqhn": h['fqhn'], 'ip': h['mainIP'],
                          "confid": conf.confid, "serial": int(time.time())}
                _result = self.getForwardName(h['fqhn'])
                if _result is None:
                    self.addWarning(h['fqhn'], "This hostname can't be "
                                   +"inserted in DNS, ignoring it.")
                else:
                    tplval["base"], zone = _result
                    filename_db = "%s/%s/dns/db.%s" \
                                  % (self.baseDir, server, zone)
                    filename_named = "%s/%s/dns/named.conf.confmgr" \
                                     % (self.baseDir, server)
                    if not os.path.exists(filename_named):
                        self.templateCreate(filename_named,
                                            templates["header_named"],
                                            {"confid": conf.confid})
                    if not os.path.exists(filename_db):
                        self.templateCreate(filename_db,
                                            templates["header_zone"],
                                            tplval)
                        self.templateAppend(filename_named,
                                            templates["zone_named"],
                                            {"zone": zone, "file": zone})
                    self.templateAppend(filename_db, templates["a"], tplval)
                _result = self.getReverseName(h['mainIP'])
                if _result is None:
                    self.addWarning(h['mainIP'], "This address can't be "
                                   +"inserted in DNS, ignoring it.")
                else:
                    tplval["revLSB"], zone = self.getReverseName(h['mainIP'])
                    filename_db = "%s/%s/dns/db.%s" \
                                  % (self.baseDir, server, zone)
                    if not os.path.exists(filename_db):
                        self.templateCreate(filename_db,
                                            templates["header_zone"],
                                            tplval)
                        self.templateAppend(filename_named,
                                            templates["zone_named"],
                                            {"zone": zone+".in-addr.arpa",
                                             "file": zone})
                    self.templateAppend(filename_db, templates["ptr"], tplval)


# vim:set expandtab tabstop=4 shiftwidth=4:
