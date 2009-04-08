################################################################################
#
# ConfigMgr Apache Reverse Proxy configuration file generator
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

"""Generator for Apache's Reverse Proxy"""

import os

import conf
from generators import Templator 

class ApacheRPTpl(Templator):
    """Generator for Apache's Reverse Proxy"""

    def generate(self):
        """Generate files"""
        templates = self.loadTemplates("apache_rp")
        seenServers = {}
        for ventilation in self.mapping.values():
            if 'apacheRP' not in ventilation :
                continue
            for i in ('nagios','storeme'):
                if i in ventilation and ventilation[i] not in seenServers:
                    seenServers[ventilation[i]] = 1
                    filename = "%s/%s/apacheRP.conf" \
                               % (self.baseDir,ventilation['apacheRP'])
                    if not os.path.exists(filename):
                        self.templateCreate(filename, templates["header"],
                                                      conf.confid)
                    self.templateAppend(filename, templates["apache"],
                                        {'server': ventilation[i]} )


# vim:set expandtab tabstop=4 shiftwidth=4:
