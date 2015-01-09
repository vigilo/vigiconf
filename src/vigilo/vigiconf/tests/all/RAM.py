# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2006-2015 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.vigiconf.lib.confclasses.test import Test



class RAM(Test):
    """Check the RAM usage for a host"""

    oids = [".1.3.6.1.2.1.25.2.3.1.2"]

    def add_test(self, **kw):
        """
        @param kw: unused (compatibility layer for other RAM tests)
        """
        # Ces classes ont de meilleurs tests de RAM.
        # Note: on ne met pas ucd dans cette liste car son test se sert des
        # indicateurs définis ici (et surcharge le graphe)
        skipclasses = [ "cisco", "windows2000", "rapidcity", "xmperf",
                        "netware", "alcatel", "expand", "extremenetworks",
                        "cisco_asa", "bluecoat", "bigip", "esxi" ]
        for skipclass in skipclasses:
            if skipclass in self.host.classes:
                return

        # Recherche du type "hrStorageRam"
        self.add_collector_metro("Used RAM", "m_table_mult", [".1.3.6.1.2.1.25.2.1.2"],
                    ["WALK/.1.3.6.1.2.1.25.2.3.1.4", "WALK/.1.3.6.1.2.1.25.2.3.1.6",
                    "WALK/.1.3.6.1.2.1.25.2.3.1.2"], "GAUGE", label="Used")
        self.add_collector_metro("Total RAM", "m_table_mult", [".1.3.6.1.2.1.25.2.1.2"],
                    ["WALK/.1.3.6.1.2.1.25.2.3.1.4", "WALK/.1.3.6.1.2.1.25.2.3.1.5",
                    "WALK/.1.3.6.1.2.1.25.2.3.1.2"], "GAUGE", label="Total")
        self.add_graph("RAM", [ "Used RAM", "Total RAM" ], "lines", "bytes",
                       group="Performance", last_is_max=True)


# vim:set expandtab tabstop=4 shiftwidth=4:
