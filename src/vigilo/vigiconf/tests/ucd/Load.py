# -*- coding: utf-8 -*-
# pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2006-2020 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from __future__ import unicode_literals

from vigilo.vigiconf.lib.confclasses.validators import arg, Float
from vigilo.vigiconf.lib.confclasses.test import Test
from vigilo.common.gettext import l_


class Load(Test):
    """Check the load of a host"""

    oids = [".1.3.6.1.4.1.2021.10.1.5.1"]

    @arg(
        'warn', Float,
        l_('WARNING threshold'),
        l_("""
            The WARNING and CRITICAL thresholds apply to the "Load 01" value,
            and are automatically computed for the "Load 05" and "Load 15"
            values by removing respectively 1 and 2 units.
        """)
    )
    @arg(
        'crit', Float,
        l_('CRITICAL threshold'),
        l_("""
            The WARNING and CRITICAL thresholds apply to the "Load 01" value,
            and are automatically computed for the "Load 05" and "Load 15"
            values by removing respectively 1 and 2 units.
        """)
    )
    def add_test(self, warn=20, crit=30):
        # Load 01
        self.add_collector_service("Load 01", "simple_factor",
                    [warn, crit, 1.0/100, "Load: %2.2f"],
                    [ "GET/.1.3.6.1.4.1.2021.10.1.5.1" ])
        self.add_collector_metro("Load 01", "directValue", [],
                    [ "GET/.1.3.6.1.4.1.2021.10.1.5.1" ], "GAUGE")
        # Load 05
        self.add_collector_service("Load 05", "simple_factor",
                    [warn-1, crit-1, 1.0/100, "Load: %2.2f"],
                    [ "GET/.1.3.6.1.4.1.2021.10.1.5.2" ])
        self.add_collector_metro("Load 05", "directValue", [],
                    [ "GET/.1.3.6.1.4.1.2021.10.1.5.2" ], "GAUGE")
        # Load 15
        self.add_collector_service("Load 15", "simple_factor",
                    [warn-2, crit-2, 1.0/100, "Load: %2.2f"],
                    [ "GET/.1.3.6.1.4.1.2021.10.1.5.3" ])
        self.add_collector_metro("Load 15", "directValue", [],
                    [ "GET/.1.3.6.1.4.1.2021.10.1.5.3" ], "GAUGE")

        self.add_graph("Load", [ "Load 01", "Load 05", "Load 15" ], "areas",
                       "load", group="Performance", factors={"Load 01": 0.01,
                                                             "Load 05": 0.01,
                                                             "Load 15": 0.01})


# vim:set expandtab tabstop=4 shiftwidth=4:
