################################################################################
#
# ConfigMgr pmacct configuration file generator
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

"""Generator for the pmacct and pmacct-snmp (netflow collector)"""

import os
import os.path
import re

from vigilo.common.conf import settings

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib.generators import FileGenerator

class NetflowGen(FileGenerator):
    """Generator for pmacct and pmacct-snmp (netflow collector)"""

    def generate_host(self, hostname, vserver):
        """Generate files"""

        #for (hostname, ventilation) in self.mapping.iteritems():
        #    if not "netflow" in ventilation:
        #        continue

        h = conf.hostsConf[hostname]
        # loads the configuration for host
        if not len(h["netflow"]): # if no netflow is configured.
            return
        print h["netflow"]

        # Set different filename for each.
        # pmacct-snmp
        # nfacctd
        # network.lst (used by nfacctd)

        self.fileName_pmacct_snmp = "%s/%s/pmacct/pmacct-snmp.conf" \
                        % (self.baseDir, vserver)
        #self.fileName_snmpd = "%s/%s/snmp/snmpd.conf" \
        #                % (self.baseDir, vserver)
        #
        # Les templates sont conserves 'au cas ou'. L'utilisation de SNMPD
        # pour faire des demandes de donnees netflow requiert une modification
        # de nfacct.conf pour une utilisation du plugin memory.
        # Plus d'infos sur le site officiel :
        # http://www.net-track.ch/opensource/pmacct-snmp/README.php
        # ou sur le wiki :
        # https://vigilo-dev/trac/wiki/Dev/Netflow

        self.fileName_nfacct = "%s/%s/pmacct/nfacct.conf" \
                        % (self.baseDir, vserver)
        self.fileName_network = "%s/%s/pmacct/networks.lst" \
                        % (self.baseDir, vserver)
        ip_list = ""
        ip_list_net = ""
        for ip in h["netflow"]["IPs"]:
            ip_list += "%s\n" % ip
            ip_, mask = ip.split("/")
            mask = str(2**(32-int(mask))-1)
            ip_list_net += "hosts: %(ip)s/%(mask)s\n" % {"ip": ip_, "mask": mask}
        # On ne veut que le sous reseau

        self.templateCreate(self.fileName_network, self.templates["networks"],
            {"ip": ip_list}
            )
        self.templateCreate(self.fileName_pmacct_snmp, self.templates["pmacct-snmp"],
            {"hosts": ip_list_net
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
