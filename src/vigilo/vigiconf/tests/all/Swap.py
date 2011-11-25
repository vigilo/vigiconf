# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221

from vigilo.vigiconf.lib.confclasses.test import Test



class Swap(Test):
    """Graph the swap usage (no supervision test)"""

    oids = [".1.3.6.1.2.1.25.2.3.1.2"]

    def add_test(self, host):
        """
        @param host: the Host object to add the test to
        """
        host.add_collector_metro("Swap", "m_table_mult",
                [".1.3.6.1.2.1.25.2.1.3"], # type: hrStorageVirtualMemory
                ["WALK/.1.3.6.1.2.1.25.2.3.1.4", "WALK/.1.3.6.1.2.1.25.2.3.1.6",
                 "WALK/.1.3.6.1.2.1.25.2.3.1.2"], 'GAUGE',
                 label='Used')
        host.add_collector_metro("swap-total", "m_table_mult", [".1.3.6.1.2.1.25.2.1.3"],
                    ["WALK/.1.3.6.1.2.1.25.2.3.1.4", "WALK/.1.3.6.1.2.1.25.2.3.1.5",
                    "WALK/.1.3.6.1.2.1.25.2.3.1.2"], "GAUGE",
                    label="Total")
        host.add_graph("Swap", [ "Swap", "swap-total" ], "stacks", "bytes",
                       last_is_max=True, min=0, group="Performance")


# vim:set expandtab tabstop=4 shiftwidth=4:
