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

"""Generator for the Collector"""

import os
import urllib

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib.generators import FileGenerator


class CollectorGen(FileGenerator):
    """Generator for the Collector"""

    def generate_host(self, hostname, vserver):
        fileName = os.path.join(self.baseDir, vserver, self.application.name,
                                "%s.pm" % hostname)
        h = conf.hostsConf[hostname]
        newhash = h.copy()
        newhash['spoolmeServer'] = self.ventilation[hostname]['nagios']
        if newhash['snmpVersion'] == '2' or newhash['snmpVersion'] == '1':
            newhash['snmpAuth'] = "communityString => '%(community)s'" \
                                  % newhash
        else:
            if newhash['snmpVersion'] == '3':
                newhash['snmpAuth'] = "'seclevel'=> '%(seclevel)s', " \
                                  +"'authproto' => '%(authproto)s', " \
                                  +"'secname' => '%(secname)s', " \
                                  +"'authpass' => '%(authpass)s'" \
                                  % newhash
        newhash['confid'] = conf.confid
        self.templateCreate(fileName, self.templates["header"], newhash)
        if len(h['SNMPJobs']):
            self.__fillsnmpjobs(hostname, fileName)
        self.templateAppend(fileName, self.COMMON_PERL_LIB_FOOTER, {})
        self.templateClose(fileName)

    def __fillsnmpjobs(self, hostname, fileName):
        """Fill the contents of the SNMP jobs file"""
        h = conf.hostsConf[hostname]
        keys = h['SNMPJobs'].keys()
        # We sort the keys to make sure we generate in the same
        # order as StoreMe
        keys.sort()
        for jobname, jobtype in keys:
            jobdata = h['SNMPJobs'][(jobname, jobtype)]
            tplvars = {'function': jobdata['function'],
                       'params': str(jobdata['params']),
                       'vars': str(jobdata['vars']),
                       'name': jobname,
                       'encodedname': "",
                       'reRouteFor': 'undef',
                      }
            # We collect data for another host, analyse the
            # reRouting arguements
            if jobdata['reRouteFor'] != None:
                forHost = jobdata['reRouteFor']['host']
                if jobtype != 'perfData': # service check result => forHost's spoolme server
                    tplvars['reRouteFor'] = "{server => '%s', " \
                                            % self.ventilation[forHost]['nagios'] \
                                            +"host => '%s', " % forHost \
                                            +"service => '%s'}" \
                                            % jobdata['reRouteFor']['service']
                service = jobdata['reRouteFor']['service']
            else:
                forHost = hostname
                service = jobname
            tplvars["encodedname"] = urllib.quote_plus(service).strip()
            if jobtype == 'perfData':
                self.templateAppend(fileName, self.templates["metro"], tplvars)
            else:
                self.templateAppend(fileName, self.templates["service"], tplvars)


# vim:set expandtab tabstop=4 shiftwidth=4:
