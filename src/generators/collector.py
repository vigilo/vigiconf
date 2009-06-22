################################################################################
#
# ConfigMgr Nagios Collector plugin configuration file generator
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

"""Generator for the Collector"""

import base64

import conf
from generators import Templator 

class CollectorTpl(Templator):
    """Generator for the Collector"""

    def generate(self):
        """Generate files"""
        templates = self.loadTemplates("collector")
        for hostname, ventilation in self.mapping.iteritems():
            if 'collector' not in ventilation:
                continue
            dirName = "%s/%s/collector" % (self.baseDir,
                                           ventilation['collector'])
            fileName = "%s/%s.pm" % (dirName, hostname)
            h = conf.hostsConf[hostname]
            newhash = h.copy()
            newhash['spoolmeServer'] = ventilation['nagios']
            newhash['storemeServer'] = ventilation['storeme']
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
            self.templateCreate(fileName, templates["header"], newhash)
            if len(h['SNMPJobs']):
                self.__fillsnmpjobs(hostname, fileName, templates)
            self.templateAppend(fileName, self.COMMON_PERL_LIB_FOOTER, {})
            self.templateClose(fileName)


    def __fillsnmpjobs(self, hostname, fileName, templates):
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
                if jobtype == 'perfData': # for the storeme server
                    tplvars['reRouteFor'] = "{server => '%s', " \
                                            % self.mapping[forHost]['storeme'] \
                                            +"port =>%s}" % 50001
                else: # service check result => forHost's spoolme server
                    tplvars['reRouteFor'] = "{server => '%s', " \
                                            % self.mapping[forHost]['nagios'] \
                                            +"port =>%s, " % 50000 \
                                            +"host => '%s', " % forHost \
                                            +"service => '%s'}" \
                                            % jobdata['reRouteFor']['service']
                service = jobdata['reRouteFor']['service']
            else:
                forHost = hostname
                service = jobname
            if conf.mode == "onedir":
                encodedservice = base64.encodestring(service).replace("/","_")
                tplvars["encodedname"] = "%s/%s" % (forHost,
                                                    encodedservice.strip())
            if jobtype == 'perfData':
                self.templateAppend(fileName, templates["metro"], tplvars)
            else:
                self.templateAppend(fileName, templates["service"], tplvars)


# vim:set expandtab tabstop=4 shiftwidth=4:
