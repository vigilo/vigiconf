# -*- coding: utf-8 -*-

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
                    directives=self.directives)
        host.add_collector_metro("TCP connections", "directValue", [], 
                    ["GET/.1.3.6.1.2.1.6.9.0"], "GAUGE")
        host.add_graph("TCP connections", [ "TCP connections" ], "lines",
                    "conns", group="Performance")


# vim:set expandtab tabstop=4 shiftwidth=4:
