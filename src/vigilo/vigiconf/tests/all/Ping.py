# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2006-2019 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from __future__ import unicode_literals

from vigilo.vigiconf.lib.confclasses.validators import arg, Struct, Integer
from vigilo.vigiconf.lib.confclasses.test import Test
from vigilo.vigiconf.lib.exceptions import ParsingError
from vigilo.common.gettext import translate, l_
_ = translate(__name__)


class Ping(Test):
    """Check if a host is up with a ping"""

    @arg(
        'warn', Struct(Integer(min=0), Integer(min=0, max=100)),
        l_('WARNING thresholds'),
        l_("""
            A list containing two WARNING thresholds.
            The first one applies to the probes' round-trip average (in ms).
            The second one applies to packet loss (as a percentage).
        """)
    )
    @arg(
        'crit', Struct(Integer(min=0), Integer(min=0, max=100)),
        l_('CRITICAL thresholds'),
        l_("""
            A list containing two CRITICAL thresholds.
            The first one applies to the probes' round-trip average (in ms).
            The second one applies to packet loss (as a percentage).
        """)
    )
    def add_test(self, warn=(3000, 20), crit=(5000, 100)):
        self.add_external_sup_service("Ping", "check_icmp!%s,%s%%!%s,%s%%" %
                                      (warn[0], warn[1], crit[0], crit[1]))
        self.add_perfdata_handler("Ping", 'Ping-loss', 'Loss', 'pl')
        self.add_perfdata_handler("Ping", 'Ping-RTA', 'Round-trip average', 'rta')
        self.add_graph("Ping", [ 'Ping-RTA', 'Ping-loss' ], 'lines', 'ms , %')

# vim:set expandtab tabstop=4 shiftwidth=4:
