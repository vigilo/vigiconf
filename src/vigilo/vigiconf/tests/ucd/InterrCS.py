# -*- coding: utf-8 -*-

class InterrCS(Test):
    """Check the Interrupts and Context Switches of a host"""

    oids = [".1.3.6.1.4.1.2021.11.59.0", ".1.3.6.1.4.1.2021.11.60.0"]

    def add_test(self, host, warn=None, crit=None):
        """Arguments:
            host:    the Host object to add the test to
            warn:    WARNING threshold
            crit:    CRITICAL threshold

        warn and crit must be tuples (max_interrupts, max_context_switches)
        """
        # Metrology
        host.add_collector_metro("Interrupts", "directValue", [], 
                    [ "GET/.1.3.6.1.4.1.2021.11.59.0" ], "COUNTER")
        host.add_collector_metro("Context Switches", "directValue", [], 
                    [ "GET/.1.3.6.1.4.1.2021.11.60.0" ], "COUNTER")
        host.add_graph("Interrupts and C.S.", [ "Interrupts","Context Switches" ],
                    "lines", "occurences", group="Performance")
        # Services
        if warn is not None and crit is not None:
            if warn[0] is not None and crit[0] is not None:
                host.add_metro_service("Interrupts", "Interrupts", warn[0], crit[0])
            if warn[1] is not None and crit[1] is not None:
                host.add_metro_service("Context Switches", "Context Switches", warn[1], crit[1])


# vim:set expandtab tabstop=4 shiftwidth=4: