# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2011-2020 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.vigiconf.lib.confclasses.test import Test


class Swap(Test):
    """Graph the device's swap usage (no supervision test)"""

    # .1.3.6.1.2.1.25.2.3.1.3 hrStorageDescr
    # .1.3.6.1.2.1.25.2.3.1.4 hrStorageAllocationUnits
    # .1.3.6.1.2.1.25.2.3.1.5 hrStorageSize
    # .1.3.6.1.2.1.25.2.3.1.6 hrStorageUsed
    oids = [".1.3.6.1.2.1.25.2.3.1.3"]

    def add_test(self):
        self.add_collector_metro("Swap", "m_table_mult",
                ["[Ss]wap [Ss]pace"],
                ["WALK/.1.3.6.1.2.1.25.2.3.1.4",
                 "WALK/.1.3.6.1.2.1.25.2.3.1.6",
                 "WALK/.1.3.6.1.2.1.25.2.3.1.3"],
                "GAUGE", label="Used")
        self.add_collector_metro("swap-total", "m_table_mult",
                ["[Ss]wap [Ss]pace"],
                ["WALK/.1.3.6.1.2.1.25.2.3.1.4",
                 "WALK/.1.3.6.1.2.1.25.2.3.1.5",
                 "WALK/.1.3.6.1.2.1.25.2.3.1.3"],
                "GAUGE", label="Total")
        self.add_graph("Swap", [ "Swap", "swap-total" ], "stacks", "bytes",
                       last_is_max=True, min=0, group="Performance")


# vim:set expandtab tabstop=4 shiftwidth=4:
