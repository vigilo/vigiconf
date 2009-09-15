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

"""Generator for NagVis"""

from __future__ import absolute_import

import os.path
import glob

from .. import conf
from . import Templator 

class NagvisTpl(Templator):
    """Generator for NagVis"""

    def generate(self):
        """Generate files"""
        if 'nagvis' not in conf.apps:
            return
        self.backends_done = []
        self.config_done = False
        self.files = {}
        self.base_x = 100
        self.base_y = 100
        self.x_offset = 300
        self.y_offset = 50
        self.nb_items_per_col = 12
        self.templates = self.loadTemplates("nagvis")
        hosts = self.mapping.keys()
        hosts.sort()
        for hostname in hosts:
            ventilation = self.mapping[hostname]
            if 'nagvis' not in ventilation:
                continue
            # Main configuration file
            self.__makemainconf(hostname)
            # Add maps
            self.__makemaps(hostname)
            # Make group hierarchy
            self.__makegroupshierarchy(hostname)
            # copy custom maps
            dirName = "%s/%s/nagvis/maps" \
                      % (self.baseDir, ventilation['nagvis'])
            for cmap in glob.glob(os.path.join(conf.CONFDIR, "filetemplates", "nagvis", "*.cfg")):
                self.copyFile(cmap, "%s/%s"%(dirName, os.path.basename(cmap)))
        self.__makedyngroups()

    def __makemainconf(self, hostname):
        """Make the main configuration file"""
        ventilation = self.mapping[hostname]
        confFileName = "%s/%s/nagvis/config.ini.php"\
                       % (self.baseDir, ventilation['nagvis'])
        # backends
        if 'nagios' in ventilation and \
                ventilation['nagios'] not in self.backends_done:
            if not os.path.exists(confFileName):
                self.templateCreate(confFileName, self.templates["backend"],
                                    {"confid": conf.confid,
                                     "name": ventilation['nagios']})
            else:
                self.templateAppend(confFileName, self.templates["backend"],
                                    {"confid": conf.confid,
                                    "name": ventilation['nagios']})
            self.backends_done.append(ventilation['nagios'])
        # config
        if not self.config_done:
            if not os.path.exists(confFileName):
                self.templateCreate(confFileName, self.templates["header"],
                                    {"confid": conf.confid})
            else:
                self.templateAppend(confFileName, self.templates["header"],
                                    {"confid": conf.confid})
            self.config_done = True

    def __makemaps(self, hostname):
        """Make group maps"""
        h = conf.hostsConf[hostname]
        if not h.has_key("otherGroups") or len(h['otherGroups']) == 0:
            return
        ventilation = self.mapping[hostname]
        newhash = h.copy()
        for i in h['otherGroups'].keys():
            if h['serverGroup'] == i:
                continue
            fileName = "%s/%s/nagvis/maps/%s.cfg" \
                       % (self.baseDir, ventilation['nagvis'],
                          i.replace(" ", ""))
            if fileName not in self.files:
                self.files[fileName] = 0
                self.templateCreate(fileName, self.templates["map"],
                                    {"confid": conf.confid, 'hostgroupName':i})
            else:
                self.files[fileName] += 1
            x = self.base_x \
                + (self.files[fileName] / self.nb_items_per_col) \
                * self.x_offset
            y = self.base_y \
                + (self.files[fileName] % self.nb_items_per_col) \
                * self.y_offset
            newhash['coord_y'] = y
            newhash['coord_services_y'] = y
            newhash['coord_metro_y'] = y
            newhash['coord_x'] = x
            newhash['coord_services_x'] = x + 32
            newhash['coord_metro_x'] = x + 64
            newhash['sup_server'] = ventilation['nagios']
            self.templateAppend(fileName, self.templates["host"], newhash)

    def __makegroupshierarchy(self, hostname):
        """Build the main map"""
        ventilation = self.mapping[hostname]
        mainFileName = "%s/%s/nagvis/maps/Main.cfg" \
                       % (self.baseDir, ventilation['nagvis'])
        self.templateCreate(mainFileName, self.templates["map"],
                            {"confid": conf.confid,
                             "hostgroupName":"Monitoring"})
        i = 0
        for i, subgroup in enumerate(conf.groupsHierarchy):
            name = subgroup.replace(" ", "")
            x = self.base_x
            y = self.base_y + i * self.y_offset
            self.templateAppend(mainFileName, self.templates["submap"],
                                {"name": name, "label": subgroup,
                                 "coord_x": x, "coord_y": y})
            fileName = "%s/%s/nagvis/maps/%s.cfg" \
                       % (self.baseDir, ventilation['nagvis'], name)
            self.templateCreate(fileName, self.templates["map"],
                                {"confid": conf.confid,
                                 "hostgroupName":subgroup})
            subbase_x = 100
            subbase_y = 100
            for j, subsubgroup in enumerate(conf.groupsHierarchy[subgroup]):
                name = subsubgroup.replace(" ", "")
                x = subbase_x
                y = subbase_y + j * self.y_offset
                self.templateAppend(fileName, self.templates["submap"],
                                    {"name": name, "label": subsubgroup,
                                     "coord_x": x, "coord_y": y})
        l = conf.dynamicGroups.keys()
        l.sort()
        i += 1
        for j in l:
            if conf.dynamicGroups[j]['show_in_main']:
                name = j.replace(" ", "")
                x = self.base_x
                y = self.base_y + i * self.y_offset
                self.templateAppend(mainFileName, self.templates["submap"],
                                    {"name": name, "label": j,
                                     "coord_x": x, "coord_y": y})
                i += 1

    def __makedyngroups(self):
        """
        Make dynamic groups
        @todo: sort this out
        """
        nagvis_server = self.__getnagvisserver()
        # stage 1: compute dynamic group members
        for group_name in conf.dynamicGroups:
            if 'group_members' not in conf.dynamicGroups[group_name]:
                conf.dynamicGroups[group_name]['group_members'] = []
            if 'host_members' not in conf.dynamicGroups[group_name]:
                conf.dynamicGroups[group_name]['host_members'] = {}
            if conf.dynamicGroups[group_name]['nagvis_server'] == None:
                if nagvis_server == None:
                    self.addError("nagvis dynamic maps", "Cannot guess nagvis "
                                 +"server for map %s, please add " % group_name
                                 +"nagvis_server argument in addGroup")
                    return
                else:
                    conf.dynamicGroups[group_name]['nagvis_server'] = \
                                                    nagvis_server
            for l in conf.dynamicGroups:
                if group_name == l or \
                        conf.dynamicGroups[l]["group_query"] == "" or \
                        not eval(conf.dynamicGroups[l]["group_query"]):
                    continue
                if "group_members" not in conf.dynamicGroups[l]:
                    conf.dynamicGroups[l]["group_members"] = []
                conf.dynamicGroups[l]["group_members"].append(group_name)
        
        for g in conf.groupsHierarchy:
            group_name = g
            for l in conf.dynamicGroups:
                if g == l or conf.dynamicGroups[l]["group_query"] == "" or \
                        not eval(conf.dynamicGroups[l]["group_query"]):
                    continue
                conf.dynamicGroups[l]["group_members"].append(group_name)
            for group_name in conf.groupsHierarchy[g]:
                for l in conf.dynamicGroups:
                    if g == l or \
                            conf.dynamicGroups[l]["group_query"] == "" or \
                            not eval(conf.dynamicGroups[l]["group_query"]):
                        continue
                    conf.dynamicGroups[l]["group_members"].append(group_name)

        
        for host_name in conf.hostsConf:
            o = conf.hostsConf[host_name]
            for k in conf.dynamicGroups:
                if conf.dynamicGroups[k]["host_query"] == "" or \
                        not eval(conf.dynamicGroups[k]["host_query"]) or \
                        host_name in conf.dynamicGroups[k]["host_members"]:
                    continue
                conf.dynamicGroups[k]["host_members"][host_name] = []
            for service_name in o['services'].keys():
                for k in conf.dynamicGroups:
                    if conf.dynamicGroups[k]["service_query"] == "" or \
                            not eval(conf.dynamicGroups[k]["service_query"]):
                        continue
                    if host_name not in conf.dynamicGroups[k]["host_members"]: 
                        conf.dynamicGroups[k]["host_members"][host_name] = []
                    conf.dynamicGroups[k]["host_members"][host_name].append(service_name)
        # stage 2: create NagVis DynGroups Maps
        for (group_name, g) in conf.dynamicGroups.iteritems():
            fileName = "%s/%s/nagvis/maps/%s.cfg" \
                       % (self.baseDir, g['nagvis_server'], group_name)
            self.templateCreate(fileName, self.templates["map"],
                                {"confid": conf.confid,
                                 "hostgroupName": g['label']})
            i = 0
            # stage 2.1 : Groups in groups
            g['group_members'].sort()
            for subgroup in g['group_members']:
                x = self.base_x + (i / self.nb_items_per_col) * self.x_offset
                y = self.base_y + (i % self.nb_items_per_col) * self.y_offset
                self.templateAppend(fileName, self.templates["submap"],
                                {"name": subgroup.replace(" ", ""),
                                 "label": conf.dynamicGroups[subgroup]["label"],
                                 "coord_x": x, "coord_y": y})
                i += 1

            # stage 2.2 : hosts with no services
            l = g['host_members'].keys()
            l.sort()
            for host_name in l:
                if len(g['host_members'][host_name]) != 0:
                    continue
                self.__makedynmap(host_name, i, fileName)
                i += 1

            # stage 2.3 : hosts and their associated services
            for host_name in l:
                g['host_members'][host_name].sort()
                for service_name in g['host_members'][host_name]:
                    self.__makedynmap(host_name, i, fileName, service_name)
                    i += 1

    def __getnagvisserver(self):
        """pre-check: autodetect the nagvis server"""
        nvservers = set()
        for appmapping in self.mapping.values():
            for app, appserver in appmapping.iteritems():
                if app != "nagvis":
                    continue
                nvservers.add(appserver)
        if len(nvservers) == 1:
            # Only one nagvis server in the conf, use this one
            nagvis_server = nvservers.pop()
        else:
            nagvis_server = None
        return nagvis_server

    def __makedynmap(self, hostname, i, fileName, service=None):
        """Make a single dynamic map"""
        h = conf.hostsConf[hostname]
        newhash = h.copy()
        x = self.base_x + (i / self.nb_items_per_col) * self.x_offset
        y = self.base_y + (i % self.nb_items_per_col) * self.y_offset
        newhash['coord_y'] = y
        newhash['coord_services_y'] = y
        newhash['coord_metro_y'] = y
        newhash['coord_x'] = x
        newhash['coord_services_x'] = x + 32
        newhash['coord_metro_x'] = x + 64
        newhash['sup_server'] = self.mapping[hostname]['nagios']
        if service is None:
            tplname = "host"
        else:
            newhash['service'] = service
            tplname = "service"
        self.templateAppend(fileName, self.templates[tplname], newhash)

# vim:set expandtab tabstop=4 shiftwidth=4:
