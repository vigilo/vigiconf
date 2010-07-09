# -*- coding: utf-8 -*-

class Users(Test):
    """Check the number of connected users"""

    oids = [".1.3.6.1.2.1.25.1.5.0"]

    def add_test(self, host, warn=50, crit=100):
        """Arguments:
            host: the Host object to add the test to
            warn: WARNING threshold
            crit: CRITICAL threshold
        """
        host.add_collector_service("Users", "thresholds_OID_simple",
                    [warn, crit, "%d users connected"], 
                    ["GET/.1.3.6.1.2.1.25.1.5.0"], weight=self.weight)
        host.add_collector_metro("Users", "directValue", [], 
                    ["GET/.1.3.6.1.2.1.25.1.5.0"], "GAUGE")
        host.add_graph("Users", [ "Users" ], "lines", "users")


# vim:set expandtab tabstop=4 shiftwidth=4:
