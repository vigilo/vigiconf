# vim: fileencoding=utf-8 sw=4 ts=4 et ai
# Copyright (C) 2007-2020 CS GROUP – France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""Generator for PerfData handler"""

import os

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib.generators import FileGenerator

class PerfDataGen(FileGenerator):
    """Generator for PerfData handler"""

    def generate_host(self, hostname, vserver):
        h = conf.hostsConf[hostname]
        if not h.has_key("PDHandlers") or len(h['PDHandlers']) == 0:
            return
        fileName = os.path.join(self.baseDir, vserver, "perfdata",
                                "perf-%s.pm" % hostname)
        newhash = h.copy()
        newhash['confid'] = conf.confid
        self.templateCreate(fileName, self.templates["header"], newhash)
        for (servicename, perfitems) in h['PDHandlers'].iteritems():
            servicename = self.quote(servicename.strip())
            for perfitem in perfitems:
                if perfitem['reRouteFor'] is not None:
                    forHost = perfitem['reRouteFor']['host']
                    reRouteFor = "'%s'" % forHost
                else:
                    forHost = hostname
                    reRouteFor = "undef"
                rrdname = self.quote(perfitem["name"].strip())
                pdvn = self.quote(perfitem['perfDataVarName'].strip())
                tplvars = {'service': servicename,
                           'host': forHost,
                           'ds': rrdname,
                           'perfDataVarName': pdvn,
                           'reRouteFor': reRouteFor}
                self.templateAppend(fileName, self.templates["map"], tplvars)
        self.templateAppend(fileName, self.COMMON_PERL_LIB_FOOTER, {})
        self.templateClose(fileName)


# vim:set expandtab tabstop=4 shiftwidth=4:
