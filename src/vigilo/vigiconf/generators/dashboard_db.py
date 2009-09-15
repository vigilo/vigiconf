################################################################################
#
# ConfigMgr Dashboard DB configuration file generator
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

"""Generator for the VigiBoard database"""
            
from __future__ import absolute_import

import os
import os.path

from .. import conf
from . import Templator 

class DashboardDBTpl(Templator):
    """Generator for the VigiBoard database"""
            
    def generate(self):
        """Generate files"""
        templates = self.loadTemplates("dashboard_db")
        tags = []
        serverList = [] 
        
        # Build the list of Dashboard servers
        for (host, ventilation) in self.mapping.iteritems():            
            if 'dashboard_db' in ventilation:
                serverList.append(ventilation['dashboard_db'])

        # Build the list of tags
        h = conf.hostsConf
        for host, host_data in h.iteritems():
            if host_data.has_key("tags"):
                for tag_name, tag_value in host_data["tags"].iteritems():
                    tags.append( (host, "", tag_name, tag_value) )
            for service, service_data in host_data["services"].iteritems():
                if service_data.has_key("tags"):
                    for tag_name, tag_value in service_data["tags"].iteritems():
                        tags.append( (host, service, tag_name, tag_value) )

        # Create the SQL files
        for server in serverList:
            dirName = "%s/%s/dashboard_db" % (self.baseDir, server)
            fileName = "%s/dashboard_db.sql" % (dirName)                    
            if os.path.exists(fileName):
                continue
            self.templateCreate(fileName, templates["header"],
                                {"confid": conf.confid})
            for host, service, tag, value in tags:
                self.templateAppend(fileName, templates["tag"], 
                    {"host":host, "service":service, "tag":tag, "value":value})


# vim:set expandtab tabstop=4 shiftwidth=4:
