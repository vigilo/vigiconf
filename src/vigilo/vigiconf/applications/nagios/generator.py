# -*- coding: utf-8 -*-
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

"""Generator for Nagios"""

from vigilo.common.conf import settings

import os.path

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib.generators import FileGenerator


class NagiosGen(FileGenerator):
    """
    This class is in charge of generating a nagios compliant configuration
    file given the internal data model of VigiConf (see conf.py)

    @todo: this really deserves a refactoring, use safety glasses
    """

    def generate(self):
        self._files = {}
        super(NagiosGen, self).generate()

    def generate_host(self, hostname, vserver):
        self.fileName = os.path.join(self.baseDir, vserver, "nagios",
                                     "nagios.cfg")
        if self.fileName not in self._files:
            self._files[self.fileName] = {}
        # loads the configuration for host
        h = conf.hostsConf[hostname]
        if not os.path.exists(self.fileName):
            # One Nagios server routes all its events to a single
            # connector-nagios instance.
            # WARNING: The first host that has to be monitored on this
            # Nagios instance gives the name of the corrsup server for
            # anyone else in this Nagios instance!!
            self.templateCreate(self.fileName, self.templates["header"],
                {"confid": conf.confid,
                 "socket": settings["vigiconf"].get("socket_nagios_to_vigilo")})
        newhash = h.copy()
        # Groups
        self.__fillgroups(hostname, newhash)
        # Notification periods
        if h.has_key("notification_period") and h["notification_period"]:
            newhash["notification_period"] = "notification_period " \
                                             + h["notification_period"]
        else:
            newhash["notification_period"] = ""
        # Dependencies
        parents = self.__getdeps(hostname)
        if parents:
            newhash['parents'] = "	parents    "+",".join(parents)
        else:
            newhash['parents'] = ""

        #   directives generiques
        newhash['generic_directives'] = ""
        for directive, value in newhash['nagiosDirectives'].iteritems():
            newhash['generic_directives'] += "%s    %s\n    " % \
                (directive, value)

        # Add the host definition
        self.templateAppend(self.fileName, self.templates["host"], newhash)

        # We need to know if a service is the exact same serviceName as ours.
        if h.has_key("snmpTrap") and len(h["snmpTrap"]):
            srvnames = h["services"].keys()
            # We can have something like:
            # {'SERVICE1': {'2.3.4.5.6': {'label': 'LAB1, 'command': '/usr/bin/cmd1', 'service': 'SERVICE1', 'address': '127.0.0.1'}}
            #, 'SERVICE2': {'1.2.3.4.5': {'label': 'LAB2', 'command': '/usr/bin/cmd2', 'service': 'SERVICE2', 'address': '127.0.0.1'}}}
            # 2 services about Trap for the same host
            for k in h["snmpTrap"]:
                if k in srvnames:
                    continue
                self.templateAppend(self.fileName, self.templates["collector"], {
                    'name' :  hostname,
                    'serviceName' : k,
                    'quietOrNot': "",
                    'notification_period': "",
                    'generic_sdirectives': "",
                     })

        # Add the service item into the Nagios configuration file
        if len(h['services']):
            if len(h['SNMPJobs']):
                # add a static actif service calling Collector if needed
                self.templateAppend(self.fileName,
                                    self.templates["collector_main"],
                                    newhash)
            self.__fillservices(hostname, newhash)

        ## WARNING: ugly hack to handle routes (GCE based, must disappear)!!
        ## unused unless your host has a '-RT-DC' in its name
        ## TODO: use tags
        #if h['name'].count('-RT-DC'):
        #    if len(h['routeItems']):
        #        for kk in self.mapping.keys():
        #            hh = conf.hostsConf[kk]
        #            if hh['name'].count('-RT-DC'):
        #                if len(hh['routeItems']):
        #                    for (kkk) in hh['routeItems'].keys():
        #                        sname = 'route '+hh['routeItems'][kkk]
        #                        self.templateAppend(self.fileName,
        #                                        self.templates["collector"],
        #                                        {'name': h['name'],
        #                                        'serviceName': sname})

    def __fillgroups(self, hostname, newhash):
        """Fill the groups in the configuration file"""
        h = conf.hostsConf[hostname]
        if h.get("otherGroups", None):
            newhash['hostGroups'] = "hostgroups %s" % \
                ','.join(h['otherGroups'])
            # builds a list of all groups memberships
            for i in h['otherGroups']:
                if i not in self._files[self.fileName]:
                    self._files[self.fileName][i] = 1
                    # @TODO: réfléchir à la gestion des groupes Nagios.
                    # L'ancien code a été conservé ci-dessous.
                    self.templateAppend(self.fileName,
                                    self.templates["hostgroup"],
                                    {"hostgroupName": i,
                                     "hostgroupAlias": i})
#                    self.templateAppend(self.fileName,
#                                    self.templates["hostgroup"],
#                                    {"hostgroupName": i,
#                                     "hostgroupAlias": conf.hostsGroups[i]})
        else:
            newhash['hostGroups'] = "# no hostgroups defined"
        newhash['quietOrNot'] = ""

    def __getdeps(self, hostname):
        """Extract the parents list"""
        h = conf.hostsConf[hostname]
        parents = []
        # looks for the dependencies defined into VigiConf
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
                parent_ventilation = self.ventilation[parenthost]["nagios"]
                if parenttype != "Host" or \
                        self.ventilation[hostname]['nagios'] != parent_ventilation:
                    continue # only host-to-host dependencies
                parents.append(parenthost)
        return parents

    def __fillservices(self, hostname, newhash):
        """Fill the services section in the configuration file"""
        h = conf.hostsConf[hostname]
        for (srvname, srvdata) in h['services'].iteritems():
            scopy = srvdata.copy()

            #   directives generiques
            generic_directives = ""
            if newhash['nagiosSrvDirs'].has_key(srvname):
                for directive, value in newhash['nagiosSrvDirs'][srvname].iteritems():
                    generic_directives += "%s    %s\n    " % (directive, value)

            if srvname  in h['PDHandlers']:
                # there is a perfdata handler to set as we asked to
                # route a perfdata (or more) to a RRD
                # (using perf2store => StoreMe)
                perfdata = "	process_perf_data       1"
            else:
                perfdata = ""
            # Handle notification periods
            if scopy.has_key("notification_period"):
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
                         "notification_period": scopy["notification_period"],
                         "generic_sdirectives": generic_directives})
            else:
                if scopy['command'].count("$METROSERVER$") > 0:
                    # Replace the keyword
                    if not self.ventilation[hostname].has_key("connector-metro"):
                        # Hey, I have no metro server! I can't check that!
                        self.addWarning(hostname, "Can't find the metro "
                                        +"server for an RRD-based service")
                    else:
                        mserver = self.ventilation[hostname]['connector-metro']
                        if isinstance(mserver, list):
                            mserver = mserver[0]
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
                         "notification_period": scopy["notification_period"],
                         "generic_sdirectives": generic_directives})


# vim:set expandtab tabstop=4 shiftwidth=4:
