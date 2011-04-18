################################################################################
#
# ConfigMgr pmacct configuration file generator
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

"""Generator for the pmacct and pmacct-snmp (netflow collector)"""

import os
import os.path

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib.generators import FileGenerator

class NetflowGen(FileGenerator):
    """Generator for pmacct and pmacct-snmp (netflow collector)"""

    def generate(self):
        super(NetflowGen, self).generate()

    def generate_host(self, hostname, vserver):
        h = conf.hostsConf[hostname]
        if not len(h["netflow"]): # if no netflow is configured.
            return
        if not self.ventilation[hostname].has_key("netflow"):
            return

        fileName_pmacct_snmp = os.path.join(
                self.baseDir,
                vserver,
                "pmacct/pmacct-snmp.conf"
                )
        fileName_network = os.path.join(self.baseDir, vserver,
                "pmacct/pmacctd-networks.lst")
        ip_list = ""
        ip_list_net = ""
        for ip in h["netflow"]["IPs"]:
            ip_list += "%s\n" % ip
            ip_, mask = ip.split("/")
            mask = str(2**(32-int(mask))-1)
            ip_list_net += "hosts: %(ip)s/%(mask)s\n" % {
                "ip": ip_,
                "mask": mask
                }
        # On ne veut que le sous reseau

        self.templateCreate(fileName_network,
                self.templates["pmacctd-networks"], {"ip": ip_list}
            )
        self.templateCreate(
                fileName_pmacct_snmp,
                self.templates["pmacct-snmp"], {
                    "hosts": ip_list_net
                }
            )
        #self.templateCreate(self.fileName_nfacct,
        #        self.templates["nfacctd"],
        #        {
        #        "port": h["netflow"]["port"],
        #        "database": h["netflow"]["database"],
        #        "tablename": h["netflow"]["tablename"],
        #        "version": h["netflow"]["version"],
        #        "pgsql_user": h["netflow"]["pgsql_user"],
        #        "pgsql_passwd": h["netflow"]["pgsql_passwd"]
        #        })

# vim:set expandtab tabstop=4 shiftwidth=4:
