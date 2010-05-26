################################################################################
#
# ConfigMgr Nagios configuration file generator
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

"""Generator for Nagios"""

from __future__ import absolute_import

from vigilo.common.conf import settings

import os.path

from .. import conf
from . import Templator 

class NagiosTpl(Templator):
    """
    This class is in charge of generating a nagios compliant configuration
    file given the internal data model of ConfMgr (see conf.py)

    WARNING: most of the followin logic assumes that:
     - there is one and one only instance of CorrSup aimed by this Nagios Server
     - there is one and one only instance of NDO aimed by this Nagios Server
     - in other words, all the hosts associated with a same Nagios instance have
       to share the same CorrSup and Nagvis instance, otherwise the generation
       will act wrongly.
    """

    def generate(self):
        """Generate files"""
        # pre-parse all the nagios-related templates
        # usually in /etc/vigilo/vigiconf/templates/nagios/*.tpl
        self.templates = self.loadTemplates("nagios")
        files = {}
        for (hostname, ventilation) in self.mapping.iteritems():
            # grab a tuple containing the name of an host to monitor and an
            # hasmap:
            # {<application name>: <server to deploy this host's conf
            #                       for this application>}
            if 'nagios' not in ventilation:
                # We are generating Nagios' configuration file, so we anly care
                # about hosts that need a Nagios configuration.
                continue
            if 'nagvis' in ventilation:
                # We also have a nagvis instance dealing with this host, so
                # make sure we create at least one time the ndo file routing to
                # the ndo server.
                # WARNING: The first host that has to be monitored on this
                # NagVis instance gives the name of the NagVis for anyone else
                # in this Nagios instance!!
                fileName = "%s/%s/ndomod.cfg" \
                           % (self.baseDir, ventilation['nagios'])
                if not os.path.exists(fileName):
                    self.templateCreate(fileName, self.templates["ndomod"], 
                                    {"confid": conf.confid,
                                     "name": ventilation["nagios"],
                                     "nagvis_server": ventilation["nagvis"]})
            self.fileName = "%s/%s/nagios.cfg" \
                            % (self.baseDir, ventilation['nagios'])
            if self.fileName not in files:
                files[self.fileName] = {}
            # loads the configuration for host 
            h = conf.hostsConf[hostname]
            if not os.path.exists(self.fileName):
                # One Nagios server routes all its events to a single CorrSup
                # instance.
                # WARNING: The first host that has to be monitored on this
                # Nagios instance gives the name of the corrsup server for
                # anyone else in this Nagios instance!!
                self.templateCreate(self.fileName, self.templates["header"],
                    {"confid": conf.confid,
                     "socket": settings["vigiconf"].get("socket_nagios_to_vigilo")})
            newhash = h.copy()
            # Groups
            self.__fillgroups(hostname, newhash, files)
            # Notification periods
            if h.has_key("notification_period") and h["notification_period"]:
                newhash["notification_period"] = "notification_period " \
                                                 + h["notification_period"]
            else:
                newhash["notification_period"] = ""
            # Dependencies
            parents = self.__getdeps(hostname, ventilation)
            if parents:
                newhash['parents'] = "	parents    "+",".join(parents)
            else:
                newhash['parents'] = ""
            
            #   directives generiques
            newhash['generic_directives'] = ""
            for dir, value in newhash['nagiosDirectives'].iteritems():
                newhash['generic_directives'] += "%s    %s\n    " % (dir, value)
                
            # Add the host definition
            self.templateAppend(self.fileName, self.templates["host"], newhash)
            # Add the service item into the Nagios configuration file
            if len(h['services']):
                if len(h['SNMPJobs']):
                    # add a static actif service calling Collector if needed
                    self.templateAppend(self.fileName,
                                        self.templates["collector_main"],
                                        newhash)
                self.__fillservices(hostname, newhash, ventilation)
            # WARNING: ugly hack to handle routes (GCE based, must disappear)!!
            # unused unless your host has a '-RT-DC' in its name
            # TODO: use tags
            if h['name'].count('-RT-DC'):
                if len(h['routeItems']):
                    for kk in self.mapping.keys():
                        hh = conf.hostsConf[kk]
                        if hh['name'].count('-RT-DC'):
                            if len(hh['routeItems']):
                                for (kkk) in hh['routeItems'].keys():
                                    sname = 'route '+hh['routeItems'][kkk]
                                    self.templateAppend(self.fileName,
                                                    self.templates["collector"],
                                                    {'name': h['name'],
                                                    'serviceName': sname})

    def __fillgroups(self, hostname, newhash, files):
        """Fill the groups in the configuration file"""
        h = conf.hostsConf[hostname]
        if h.has_key("otherGroups") and len(h['otherGroups']):
            newhash['hostGroups'] = "hostgroups %s" \
                                    % ','.join(h['otherGroups'].keys())
            # builds a list of all groups memberships
            for i in h['otherGroups'].keys():
                if i not in files[self.fileName]:
                    files[self.fileName][i] = 1
                    self.templateAppend(self.fileName,
                                    self.templates["hostgroup"],
                                    {"hostgroupName": i,
                                     "hostgroupAlias": conf.hostsGroups[i]})
        else:
            newhash['hostGroups'] = "# no hostgroups defined"
        # WARNING: Ugly hask, use a hard-coded membership in an group to
        # make notifications silent or not !!!
        # TODO: use tags
        if "PrepaInstallation" in h['otherGroups']:
            newhash['quietOrNot'] = "	notifications_enabled   0"
        else:
            newhash['quietOrNot'] = ""

    def __getdeps(self, hostname, ventilation):
        """Extract the parents list"""
        h = conf.hostsConf[hostname]
        parents = []
        # looks for the dependencies defined into ConfMgr
        # (addDependency(...)) and extract a subset of them, only the ones
        # that can be written into Nagios dependancy system, which is
        # too limited for our use
        for (hostname, hosttype) in conf.dependencies.keys():
            if hostname != h['name'] or hosttype != "Host":
                continue # not us
            d = conf.dependencies[(hostname, hosttype)]["deps"]
            if len(d["and"]) >= 2:
                continue # we only deal with "or"-type dependencies
            for (parenthost, parenttype) in d["or"] + d["and"]:
                parent_ventilation = self.mapping[parenthost]["nagios"]
                if parenttype != "Host" or \
                        ventilation['nagios'] != parent_ventilation:
                    continue # only host-to-host dependencies
                parents.append(parenthost)
        return parents

    def __fillservices(self, hostname, newhash, ventilation):
        """Fill the services section in the configuration file"""
        h = conf.hostsConf[hostname]
        for (srvname, srvdata) in h['services'].iteritems():
            scopy = srvdata.copy()

            #   directives generiques
            generic_directives = ""
            if newhash['nagiosSrvDirs'].has_key(srvname):
                for dir, value in newhash['nagiosSrvDirs'][srvname].iteritems():
                    generic_directives += "%s    %s\n    " % (dir, value)
            
            if srvname  in h['PDHandlers']:
                # there is a perfdata handler to set as we asked to
                # route a perfdata (or more) to a RRD
                # (using perf2store => StoreMe)
                perfdata = "	process_perf_data       1"
            else:
                perfdata = ""
            # Handle notification periods
            if copy.has_key("notification_period"):
                scopy["notification_period"] = "notification_period " \
                                            + scopy["notification_period"]
            else:
                scopy["notification_period"] = ""
            if scopy['type'] == 'passive':
                # append a passive service template
                self.templateAppend(self.fileName, self.templates["collector"],
                        {'name': h['name'],
                         'serviceName': srvname,
                         'quietOrNot': newhash['quietOrNot'],
                         'perfDataOrNot': perfdata,
                         'maxchecks': scopy.get('maxchecks', 1),
                         "notification_period": scopy["notification_period"],
                         "generic_sdirectives":generic_directives})
            else:
                if scopy['command'].count("$METROSERVER$") > 0:
                    # Replace the keyword
                    if not ventilation.has_key("storeme"):
                        # Hey, I have no metro server! I can't check that!
                        self.addWarning(hostname, "Can't find the metro "
                                        +"server for an RRD-based service")
                    else:
                        mserver = ventilation['storeme']
                        newcmd = scopy['command']
                        newcmd = newcmd.replace("$METROSERVER$", mserver)
                        scopy['command'] = newcmd
                # append an active service, nammed external, as "not handled by
                # Collector"
                self.templateAppend(self.fileName, self.templates["ext"],
                        {'name': h['name'],
                         'desc': srvname,
                         'command': scopy['command'],
                         'quietOrNot': newhash['quietOrNot'],
                         'perfDataOrNot': perfdata,
                         'maxchecks': scopy.get('maxchecks', 1),
                         "notification_period": scopy["notification_period"],
                         "generic_sdirectives":generic_directives})


# vim:set expandtab tabstop=4 shiftwidth=4:
