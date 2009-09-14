# -*- coding: utf-8 -*-

class Load(Test):
    """Check the load of a host"""

    oids = [".1.3.6.1.4.1.2021.10.1.5.1"]

    def add_test(self, host, warn=20, crit=30):
        """Arguments:
            host:    the Host object to add the test to
            warn:    WARNING threshold
            crit:    CRITICAL threshold

            The warning and critical thresholds apply to the "Load 01" value, 
            and are automatically computed for the "Load 05" and "Load 15" values
            by removing respectively 1 and 2 units.
        """
        # Load 01
        host.add_collector_service("Load 01", "simple_factor",
                    [warn, crit, 1.0/100, "Load: %2.2f"], 
                    [ "GET/.1.3.6.1.4.1.2021.10.1.5.1" ])
        host.add_collector_metro("Load 01", "directValue", [], 
                    [ "GET/.1.3.6.1.4.1.2021.10.1.5.1" ], "GAUGE")
        # Load 05
        host.add_collector_service("Load 05", "simple_factor",
                    [warn-1, crit-1, 1.0/100, "Load: %2.2f"], 
                    [ "GET/.1.3.6.1.4.1.2021.10.1.5.2" ])
        host.add_collector_metro("Load 05", "directValue", [], 
                    [ "GET/.1.3.6.1.4.1.2021.10.1.5.2" ], "GAUGE")
        # Load 01
        host.add_collector_service("Load 15", "simple_factor",
                    [warn-2, crit-2, 1.0/100, "Load: %2.2f"], 
                    [ "GET/.1.3.6.1.4.1.2021.10.1.5.3" ])
        host.add_collector_metro("Load 15", "directValue", [], 
                    [ "GET/.1.3.6.1.4.1.2021.10.1.5.3" ], "GAUGE")

        host.add_graph("Load", [ "Load 01","Load 05","Load 15" ], "areas",
                    "load", group="Performance", factors={"Load 01": 0.01,
                                                                   "Load 05": 0.01,
                                                                   "Load 15": 0.01})


# vim:set expandtab tabstop=4 shiftwidth=4:
