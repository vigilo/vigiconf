################################################################################
#
# VigiConf
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

import urllib

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib.generators import FileGenerator

class PerfDataGen(FileGenerator):
    """Generator for PerfData handler"""

    def generate(self):
        """Generate files"""
        for (hostname, ventilation) in self.mapping.iteritems():
            if 'perfdata' not in ventilation:
                continue
            h = conf.hostsConf[hostname]
            if not h.has_key("PDHandlers") or len(h['PDHandlers']) == 0:
                continue
            dirName = "%s/%s/perfdata" % (self.baseDir, ventilation['perfdata'])
            fileName = "%s/perf-%s.pm" % (dirName, hostname)
            newhash = h.copy()
            newhash['confid'] = conf.confid
            self.templateCreate(fileName, self.templates["header"], newhash)
            for (servicename, perfitems) in h['PDHandlers'].iteritems():
                for perfitem in perfitems:
                    if perfitem['reRouteFor'] != None:
                        forHost = perfitem['reRouteFor']['host']
                        reRouteFor = "'%s'" % forHost
                    else:
                        forHost = hostname
                        reRouteFor = "undef"
                    rrdname = urllib.quote_plus(perfitem["name"].strip())
                    tplvars = {'service':servicename,
                               'host': forHost, 
                               'ds': rrdname,
                               'perfDataVarName': perfitem['perfDataVarName'],
                               'reRouteFor': reRouteFor}
                    self.templateAppend(fileName, self.templates["map"], tplvars)
            self.templateAppend(fileName, self.COMMON_PERL_LIB_FOOTER, {})
            self.templateClose(fileName)


# vim:set expandtab tabstop=4 shiftwidth=4:
