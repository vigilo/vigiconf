# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2006-2020 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.vigiconf.lib.confclasses.test import Test


class RAM(Test):
    """Check the RAM usage for a host"""

    oids = [".1.3.6.1.2.1.25.2.3.1.2"]

    def add_test(self):
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
