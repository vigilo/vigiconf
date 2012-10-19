# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2006-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.vigiconf.lib.confclasses.test import Test
from vigilo.vigiconf.lib.exceptions import ParsingError
from vigilo.common.gettext import translate
_ = translate(__name__)


class Ping(Test):
    """Check if a host is up with a ping"""

    def add_test(self, warn=None, crit=None):
        """
        @param warn: La limite WARNING sous la forme d'une liste contenant
            deux éléments : C{round_trip_average, packet_loss_percent}
        @param crit: La limite CRITICAL sous la forme d'une liste contenant
            deux éléments : C{round_trip_average, packet_loss_percent}
        """
        # Seuils par défaut.
        if warn is None:
            warn = (3000, 20)
        if crit is None:
            crit = (5000, 100)

        # Validation des arguments.
        thresholds = {'warn': warn, 'crit': crit}
        for param, value in thresholds.iteritems():
            if not isinstance(value, tuple) or len(value) != 2:
                raise ParsingError(
                    _('"%s" should be a list with two values') % param)
        warn = [ self.as_int(th) for th in warn ]
        crit = [ self.as_int(th) for th in crit ]

        # Ajout des tests.
        self.add_external_sup_service("Ping", "check_icmp!%s,%s%%!%s,%s%%" %
                                      (warn[0], warn[1], crit[0], crit[1]))
        self.add_perfdata_handler("Ping", 'Ping-loss', 'Loss', 'pl')
        self.add_perfdata_handler("Ping", 'Ping-RTA', 'Round-trip average', 'rta')
        self.add_graph("Ping", [ 'Ping-RTA', 'Ping-loss' ], 'lines', 'ms , %')

# vim:set expandtab tabstop=4 shiftwidth=4:
