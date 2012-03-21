# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2006-2011 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.vigiconf.lib.confclasses.test import Test



class TCPConn(Test):
    """Check the total number of TCP connections"""

    oids = [".1.3.6.1.2.1.6.9.0"]

    def add_test(self, host, warn=1000, crit=3000):
        """Arguments:
            host: the Host object to add the test to
            warn: WARNING threshold
            crit: CRITICAL threshold
        """
        host.add_collector_service("TCP connections", "thresholds_OID_simple",
                    [warn, crit, "%d established TCP connections"],
                    ["GET/.1.3.6.1.2.1.6.9.0"], weight=self.weight,
                    warning_weight=self.warning_weight,
                    directives=self.directives)
        host.add_collector_metro("TCP connections", "directValue", [],
                    ["GET/.1.3.6.1.2.1.6.9.0"], "GAUGE",
                    rra_template="discrete")
        host.add_graph("TCP connections", [ "TCP connections" ], "lines",
                    "conns", group="Performance")


# vim:set expandtab tabstop=4 shiftwidth=4:
