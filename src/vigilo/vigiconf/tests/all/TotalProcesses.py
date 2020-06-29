# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2006-2020 CS GROUP – France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from __future__ import unicode_literals

from vigilo.vigiconf.lib.confclasses.validators import arg, Threshold
from vigilo.vigiconf.lib.confclasses.test import Test
from vigilo.common.gettext import l_


class TotalProcesses(Test):
    """Check the total number of running processes"""

    oids = [".1.3.6.1.2.1.25.1.6.0"]

    @arg('warn', Threshold, l_('WARNING threshold'))
    @arg('crit', Threshold, l_('CRITICAL threshold'))
    def add_test(self, warn=500, crit=1000):
        self.add_collector_service("Processes", "thresholds_OID_simple",
                    [warn, crit, "%d process(es) running"],
                    ["GET/.1.3.6.1.2.1.25.1.6.0"])
        self.add_collector_metro("Processes", "directValue", [],
                    ["GET/.1.3.6.1.2.1.25.1.6.0"], "GAUGE",
                    rra_template="discrete")
        self.add_graph("Total processes", [ "Processes" ], "lines",
                    "process(es)", group="Processes")


# vim:set expandtab tabstop=4 shiftwidth=4:
