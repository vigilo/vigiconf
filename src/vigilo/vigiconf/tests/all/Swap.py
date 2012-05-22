# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2011-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.vigiconf.lib.confclasses.test import Test



class Swap(Test):
    """Graph the swap usage (no supervision test)"""

    oids = [".1.3.6.1.2.1.25.2.3.1.2"]

    def add_test(self):
        """
        Teste la quantité de Swap utilisée.
        """
        self.add_collector_metro("Swap", "m_table_mult",
                [".1.3.6.1.2.1.25.2.1.3"], # type: hrStorageVirtualMemory
                ["WALK/.1.3.6.1.2.1.25.2.3.1.4", "WALK/.1.3.6.1.2.1.25.2.3.1.6",
                 "WALK/.1.3.6.1.2.1.25.2.3.1.2"], 'GAUGE',
                 label='Used')
        self.add_collector_metro("swap-total", "m_table_mult", [".1.3.6.1.2.1.25.2.1.3"],
                    ["WALK/.1.3.6.1.2.1.25.2.3.1.4", "WALK/.1.3.6.1.2.1.25.2.3.1.5",
                    "WALK/.1.3.6.1.2.1.25.2.3.1.2"], "GAUGE",
                    label="Total")
        self.add_graph("Swap", [ "Swap", "swap-total" ], "stacks", "bytes",
                       last_is_max=True, min=0, group="Performance")


# vim:set expandtab tabstop=4 shiftwidth=4:
