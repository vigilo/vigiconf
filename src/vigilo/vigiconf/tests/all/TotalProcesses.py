# -*- coding: utf-8 -*-

class TotalProcesses(Test):
    """Check the total number of running processes"""

    oids = [".1.3.6.1.2.1.25.1.6.0"]

    def add_test(self, host, warn=500, crit=1000):
        """Arguments:
            host: the Host object to add the test to
            warn: WARNING threshold
            crit: CRITICAL threshold
        """
        host.add_collector_service("Processes", "thresholds_OID_simple",
                    [warn, crit, "%d process(es) running"], 
                    ["GET/.1.3.6.1.2.1.25.1.6.0"], weight=self.weight)
        host.add_collector_metro("Processes", "directValue", [], 
                    ["GET/.1.3.6.1.2.1.25.1.6.0"], "GAUGE")
        host.add_graph("Total processes", [ "Processes" ], "lines",
                    "process(es)", group="Processes")


# vim:set expandtab tabstop=4 shiftwidth=4:
