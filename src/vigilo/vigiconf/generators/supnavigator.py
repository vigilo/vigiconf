################################################################################
#
# ConfigMgr Supervision Navigator configuration file generator
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

"""Generator for the graph navigator"""

from __future__ import absolute_import

import os
import os.path

from .. import conf
from . import Templator 

class SupNavigatorTpl(Templator):
    """Generator for the graph navigator"""

    def generate(self):
        """Generate files"""
        templates = self.loadTemplates("supnavigator")
        for (hostname, ventilation) in self.mapping.iteritems():
            if 'supnav' not in ventilation:
                continue
            fileName = "%s/%s/navconf.py" \
                       % (self.baseDir, ventilation['supnav'])
            h = conf.hostsConf[hostname]
            if not os.path.exists(fileName):
                self.templateCreate(fileName, templates["header"],
                                    {'groupsHierarchy':conf.groupsHierarchy,
                                     "confid": conf.confid,
                                     "hostsGroups":conf.hostsGroups})
            newhash = h.copy()
            newhash['supServer'] = self.mapping[hostname]['nagios']
            newhash['metroServer'] = self.mapping[hostname]['rrdgraph']
            newhash['reportingServer'] = self.mapping[hostname]['reportingv2']
            g = newhash['otherGroups'].keys()
            g.remove(newhash['serverGroup'])
            newhash['otherGroups'] = str(g)
            self.templateAppend(fileName, templates["host"], newhash)
            for (k2, v2) in h['graphGroups'].iteritems():
                self.templateAppend(fileName, templates["graph"],
                                    {'name':hostname, "groupName":k2,
                                     "graphs":str(list(v2))})
            
            # Add data for the reports into the file
            # /etc/vigilo-supnavigator/navconf.py using the file
            # /etc/vigilo-vigiconf/templates/supnavigator/reports.tpl
            self.templateAppend(fileName,
                                templates['reports'],
                                {'name':hostname,
                                'reportsettings':h['reports']})


# vim:set expandtab tabstop=4 shiftwidth=4:
