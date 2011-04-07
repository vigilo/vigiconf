# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903

from vigilo.vigiconf.lib.confclasses.test import Test



class Swap(Test):
    """Graph the swap usage (no supervision test)"""

    oids = [".1.3.6.1.2.1.25.2.3.1.2"]

    def add_test(self, host):
        """Arguments:
            host:     the Host object to add the test to
        """
        parttype = ".1.3.6.1.2.1.25.2.1.3" # type: hrStorageVirtualMemory
        oids = ["WALK/.1.3.6.1.2.1.25.2.3.1.4", "WALK/.1.3.6.1.2.1.25.2.3.1.6", "WALK/.1.3.6.1.2.1.25.2.3.1.2"]
        host.add_collector_metro("Swap", "m_table_mult", [parttype], oids, 'GAUGE')
        host.add_graph("Swap partition", [ "Swap" ], "lines", "bytes", group="Performance")


# vim:set expandtab tabstop=4 shiftwidth=4:
