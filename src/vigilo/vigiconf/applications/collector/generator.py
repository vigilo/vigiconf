# -*- coding: utf-8 -*-
# Copyright (C) 2007-2016 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""Generator for the Collector"""

import os

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib.generators import FileGenerator


class CollectorGen(FileGenerator):
    """Generator for the Collector"""

    def generate_host(self, hostname, vserver):
        fileName = os.path.join(self.baseDir, vserver, self.application.name,
                                "%s.pm" % hostname)
        h = conf.hostsConf[hostname]
        newhash = h.copy()
        if newhash['snmpVersion'] == '2' or newhash['snmpVersion'] == '1':
            newhash['snmpAuth'] = "communityString => '%(snmpCommunity)s'" \
                                  % newhash
        else:
            if newhash['snmpVersion'] == '3':
                # Récupère les paramètres de l'authentification en v3.
                # (snmpSeclevel, snmpSecname, etc.)
                snmpAuth = []
                for snmpV3Param in (
                    'Context',
                    'Seclevel',
                    'Secname',
                    'Authproto',
                    'Authpass',
                    'Privproto',
                    'Privpass'):
                    if newhash.get('snmp' + snmpV3Param):
                        snmpAuth.append("'%s' => '%s'" % (
                            snmpV3Param.lower(),
                            newhash['snmp' + snmpV3Param]
                        ))
                newhash['snmpAuth'] = u', '.join(snmpAuth)

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
            jobdata['params'] = self._convert_list(jobdata['params'])
            jobdata['vars'] = self._convert_list(jobdata['vars'])
            # échapemment des slashs et des quotes simple
            jobname = self.quote(jobname.strip())
            tplvars = {'function': jobdata['function'],
                       'params': jobdata['params'],
                       'vars': jobdata['vars'],
                       'name': jobname,
                       'dsname': jobname,
                       'reRouteFor': 'undef',
                      }
            # We collect data for another host, analyse the
            # reRouting arguements
            if jobdata['reRouteFor'] is not None:
                rr_tpl = "{vserver => '%s', host => '%s', service => '%s'}"
                forHost = jobdata['reRouteFor']['host']
                service = self.quote(jobdata['reRouteFor']['service'].strip())
                tplvars["dsname"] = service
                vserver = self.ventilation[forHost]['nagios']
                if isinstance(vserver, list):
                    vserver = vserver[0]
                if jobtype != 'perfData': # service check result => forHost's spoolme server
                    tplvars['reRouteFor'] = rr_tpl % (vserver, forHost,
                                                      service)

            if jobtype == 'perfData':
                self.templateAppend(fileName, self.templates["metro"], tplvars)
            else:
                self.templateAppend(fileName, self.templates["service"],
                                    tplvars)

    def _convert_list(self, l):
        """Convertit en syntaxe Perl en protégeant contre l'unicode (#882)"""
        result = []
        for index, param in enumerate(l):
            if isinstance(param, basestring):
                result.append("'%s'" % self.quote(param))
            else:
                result.append(repr(param))
        result = "[%s]" % ", ".join(result)
        return result

# vim:set expandtab tabstop=4 shiftwidth=4:
