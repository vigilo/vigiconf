################################################################################
#
# ConfigMgr Nagios perfdata 2 StoreMe plugin configuration generator
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

"""Generator for PerfData handler"""

import base64

import conf
from generators import Templator 

class PerfDataTpl(Templator):
    """Generator for PerfData handler"""

    def generate(self):
        """Generate files"""
        templates = self.loadTemplates("perfdata")
        for (hostname, ventilation) in self.mapping.iteritems():
            if 'perfdata' not in ventilation or 'storeme' not in ventilation:
                continue
            h = conf.hostsConf[hostname]
            if not h.has_key("PDHandlers") or len(h['PDHandlers']) == 0:
                continue
            dirName = "%s/%s/perfdata" % (self.baseDir, ventilation['perfdata'])
            fileName = "%s/perf-%s.pm" % (dirName, hostname)
            newhash = h.copy()
            newhash['storemeServer'] = ventilation['storeme']
            newhash['confid'] = conf.confid
            self.templateCreate(fileName, templates["header"], newhash)
            for (servicename, perfitems) in h['PDHandlers'].iteritems():
                for perfitem in perfitems:
                    if perfitem['reRouteFor'] != None:
                        forHost = perfitem['reRouteFor']['host']
                        reRouteFor = '{server => "%s", port => "50001"}' \
                                     % (self.mapping[forHost]['storeme'])
                    else:
                        forHost = hostname
                        reRouteFor = "undef"
                    rrdname = base64.encodestring(perfitem["name"])
                    rrdname = rrdname.replace("/", "_").strip()
                    tplvars = {'service':servicename,
                               'dsid': "%s/%s" % (forHost, rrdname),
                               'perfDataVarName': perfitem['perfDataVarName'],
                               'reRouteFor': reRouteFor}
                    self.templateAppend(fileName, templates["map"], tplvars)
            self.templateAppend(fileName, self.COMMON_PERL_LIB_FOOTER, {})
            self.templateClose(fileName)


# vim:set expandtab tabstop=4 shiftwidth=4:
