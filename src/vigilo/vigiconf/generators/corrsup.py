################################################################################
#
# ConfigMgr CorrSup configuration file generator
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

"""Generator for the correlator (CorrSup)"""

from __future__ import absolute_import

import os

from vigilo.common.conf import settings

from .. import conf
from . import Templator 

class CorrSupTpl(Templator):
    """Generator for the correlator (CorrSup)"""

    def generate(self):
        """Generate files"""
        templates = self.loadTemplates("corrsup")
        perlLibs = {}
        for host, ventilation in self.mapping.iteritems():
            if not 'corrsup' in ventilation.keys():
                # is this host handled by a corrsup server ?
                # if not, continue with next host
                continue
            dirName = "%s/%s/corrsup" % (self.baseDir, ventilation['corrsup'])
            for i in ('correl.sec', 'reduct.sec', 'transl.sec'):
                # statically copy the 3 base S.E.C. configuration files
                self.copyFile("%s/corrsup/%s" % (
                    os.path.join(settings["vigiconf"].get("confdir"),
                                 "filetemplates"), i),
                              "%s/%s" % (dirName, i))
            if not os.path.exists("%s/graph.txt" % dirName):
                self.templateCreate("%s/graph.txt" % dirName, "%s", "")
            h = conf.hostsConf[host]
            # Weight
            if not h.has_key("weight"):
#                self.addWarning(host, "no weight defined, using 100.")
                h["weight"] = 100
            self.templateAppend("%s/graph.txt" % dirName, "%s.Host=weight=%d\n",
                                                        (host, h["weight"]))
            ############# deal with CTIs ############################
            # CTI are a simple map(host, server) => aInt
            fileName = "%s/CTI.pm" % dirName
            if not os.path.exists(fileName):
                self.templateCreate(fileName, templates["cti_header"],
                                    {"confid": conf.confid})
                perlLibs[fileName] = 1
            self.templateAppend(fileName, templates["cti_host"],
                                {"host": host,
                                 "cti": conf.hostsConf[host]['cti']})
            for (service, details) in \
                        conf.hostsConf[host]['services'].iteritems():
                self.templateAppend(fileName, templates["cti_service"],
                                    {"host":host, "service": service,
                                     "cti":details["cti"]})
                # All services depend on the Host that contain it. Add
                # a simple rule for this
                self.templateAppend("%s/graph.txt" % dirName,
                                    "%s.%s=and(%s.Host),hide_this_impact\n",
                                    (host, service, host))
            ########## deal with Recette hosts #######
            # TODO This name is supposed to change !!!
            fileName = "%s/Recette.pm" % dirName
            if not os.path.exists(fileName):
                self.templateCreate(fileName, templates["recette_header"],
                                    {"confid": conf.confid})
                perlLibs[fileName] = 1
            if 'Recette' in h['otherGroups']:
                self.templateAppend(fileName, templates["recette_host"],
                                    {"host":host})
            ########## deal with Notification Servers #######
            # Notification servers are selected in this order :
            #  * if the serverGroup of this host has a statically set notif
            #    server, add it
            #  * adds then the notif server that are inherited by the host
            #    groups
            #  * if no notif server has been found so far, fall back by using
            #    the default one (configuration wide)
            fileName = "%s/Notif.pm" % dirName
            if not os.path.exists(fileName):
                self.templateCreate(fileName, templates["notif_header"],
                                    {"confid": conf.confid})
                perlLibs[fileName] = 1
            notifservers = []
            if h["serverGroup"] in conf.notificationServers.keys():
                notifservers.extend(conf.notificationServers[h["serverGroup"]])
            for og in h['otherGroups']:
                if og in conf.notificationServers.keys():
                    add_dests = conf.notificationServers[og]
                    for dest in add_dests:
                        if dest not in notifservers:
                            notifservers.append(dest)
            if not notifservers:
                notifservers = [conf.defaultNotificationServer, ]
            self.templateAppend(fileName, "$notif{\"%s\"}=[\"%s\"];\n",
                                (h["name"], '","'.join(notifservers) ))
        # Build up the Dependencies list
        all_deps = {}
        for (name, service), deps in conf.dependencies.iteritems():
            if conf.hostsConf.has_key(name): # not virtual
                if not self.mapping[name].has_key("corrsup"):
                    self.addError(name,
                                 "has dependencies but no corrsup mapping")
                    continue
                server = self.mapping[name]["corrsup"]
            else:
                server = self.findServerForVirtualHost(name)
                if not server:
                    self.addError(name, "has no server for corrsup")
                    continue
            dirName = "%s/%s/corrsup" % (self.baseDir, server)
            line = "%s.%s=" # will be filled by templateAppend
            deps_list = set()
            for dep_type in deps["deps"].keys():
                if len(deps["deps"][dep_type]) == 0:
                    continue
                real_deps = []
                for dep in deps["deps"][dep_type]: # format: (host, service)
                    if not conf.hostsConf.has_key(dep[0]): # virtual
                        real_deps.append(dep[0]) 
                    else:
                        real_deps.append("%s.%s" % dep)
                    deps_list.add(dep[0]) # add hostname for integrity check
                line += "%s(%s)" % (dep_type, ",".join(real_deps))
            if len(deps["options"]) > 0:
                line += ",%s" % ",".join(deps["options"])
            line += "\n"
            self.templateAppend("%s/graph.txt"%dirName, line, (name, service))
            self.templateAppend("%s/CTI.pm"%dirName, templates["cti_service"],
                                {"host": name , "service": service,
                                 "cti": deps['cti']})
            # add to integrity check
            all_deps[name] = deps_list

        ## Integrity check : all dependencies must exist
        # compute list of objects which have a dependency
        has_deps = [ d[0] for d in conf.dependencies.keys() ]
        # check if all dependencies are either real hosts or virtual hosts
        for host, deps in all_deps.iteritems():
            for dep in deps:
                if dep not in conf.hostsConf.keys() and dep not in has_deps:
                    self.addError(dep, "host '%s' depends on it, " % host 
                                      +"but it is neither real nor virtual !")
        for i in perlLibs.keys():
            self.templateAppend(i, self.COMMON_PERL_LIB_FOOTER, {})
            
    def findServerForVirtualHost(self, vhost):
        """
        Find the server of the first non-virtual dependency.
        @warning: This method is recursive, use with care.
        """
        server = ""
        dependencies = []
        for origin, deps in conf.dependencies.iteritems():
            name = origin[0]
            if name != vhost:
                continue
            for dep_list in deps["deps"].values():
                for dep in dep_list: # dep format: (host, service)
                    dependencies.append(dep[0])
        for dep in dependencies:
            if not conf.hostsConf.has_key(dep):
                # try to find a non-virtual host
                continue
            if not self.mapping[dep].has_key("corrsup"):
                # No corrsup ventilation for this host, try the next one
                continue
            return self.mapping[dep]["corrsup"]
        # No non-virtual hosts, recurse :(
        for dep in dependencies:
            server = self.findServerForVirtualHost(dep)
            if server:
                return server


# vim:set expandtab tabstop=4 shiftwidth=4:
