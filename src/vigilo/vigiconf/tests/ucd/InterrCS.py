# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2006-2013 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.vigiconf.lib.confclasses.test import Test



class InterrCS(Test):
    """Check the Interrupts and Context Switches of a host"""

    oids = [".1.3.6.1.4.1.2021.11.59.0", ".1.3.6.1.4.1.2021.11.60.0"]

    def add_test(self, warn=None, crit=None):
        """
        The parameters L{warn} and L{crit} must be tuples C{(max_interrupts,
        max_context_switches)}.

        @param warn: WARNING threshold
        @param crit: CRITICAL threshold
        """
        # Metrology
        self.add_collector_metro("Interrupts", "directValue", [],
                    [ "GET/.1.3.6.1.4.1.2021.11.59.0" ], "COUNTER")
        self.add_collector_metro("Context Switches", "directValue", [],
                    [ "GET/.1.3.6.1.4.1.2021.11.60.0" ], "COUNTER")
        self.add_graph("Interrupts and C.S.", [ "Interrupts","Context Switches" ],
                    "lines", "occurences", group="Performance")
        # Services
        if warn is not None and crit is not None:
            if warn[0] is not None and crit[0] is not None:
                self.add_metro_service("Interrupts", "Interrupts",
                                       warn[0], crit[0])
            if warn[1] is not None and crit[1] is not None:
                self.add_metro_service("Context Switches", "Context Switches",
                                       warn[1], crit[1])


# vim:set expandtab tabstop=4 shiftwidth=4:
