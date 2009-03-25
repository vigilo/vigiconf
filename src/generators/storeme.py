################################################################################
#
# ConfigMgr RRD StoreMe daemon configuration file generator
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

"""Generator for StoreMe, the RRD graph generator"""

import os.path
import base64

import conf
from generators import Templator 

class StoreMeTpl(Templator):
    """Generator for StoreMe, the RRD graph generator"""

    def generate(self):
        """Generate files"""
        templates = self.loadTemplates("storeme")
        #from pprint import pprint; pprint(templates)
        for (hostname, ventilation) in self.mapping.iteritems():
            if 'storeme' not in ventilation:
                continue
            h = conf.hostsConf[hostname]
            if not h.has_key("dataSources") or len(h['dataSources']) == 0:
                continue
            fileName = "%s/%s/storeme.conf.py" \
                       % (self.baseDir, ventilation['storeme'])
            if not os.path.exists(fileName):
                self.templateCreate(fileName, templates["header"],
                                    {"confid":conf.confid})
            if conf.mode != "onedir":
                self.templateAppend(fileName, templates["host"],
                                    {'host':hostname})
            keys = h['dataSources'].keys()
            keys.sort()
            for k2 in keys:
                v2 = h['dataSources'][k2]
                tplvars = {'host':hostname, 'dsType':v2['dsType'],
                           'dsName':k2, 'label':v2["label"]}
                if conf.mode == "onedir":
                    rrdname = base64.encodestring(k2).replace("/", "_").strip()
                    tplvars["host"] = "%s/%s" % (hostname, rrdname)
                    tplvars["dsName"] = "DS"
                    self.templateAppend(fileName, templates["host"],
                                        {'host':tplvars["host"]})
                self.templateAppend(fileName, templates["ds"], tplvars)


# vim:set expandtab tabstop=4 shiftwidth=4:
