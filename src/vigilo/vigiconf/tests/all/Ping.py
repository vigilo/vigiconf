# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2006-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.vigiconf.lib.confclasses.test import Test



class Ping(Test):
    """Check if a host is up with a ping"""

    def add_test(self, warn="3000,20", crit="5000,100"):
        """
        @param warn: La limite WARNING sous forme d'une chaîne à deux
            éléments séparés par une virgule :
            C{round_trip_average, packet_loss_percent}
        @param crit: La limite CRITICAL sous forme d'une chaîne à deux
            éléments séparés par une virgule :
            C{round_trip_average, packet_loss_percent}
        """
        warn = [ e.strip() for e in warn.split(",") ]
        crit = [ e.strip() for e in crit.split(",") ]
        self.add_external_sup_service("Ping", "check_ping!%s,%s%%!%s,%s%%" %
                                      (warn[0], warn[1], crit[0], crit[1]))
        self.add_perfdata_handler("Ping", 'Ping-loss', 'Loss', 'pl')
        self.add_perfdata_handler("Ping", 'Ping-RTA', 'Round-trip average', 'rta')
        self.add_graph("Ping", [ 'Ping-RTA', 'Ping-loss' ], 'lines', 'ms , %')

# vim:set expandtab tabstop=4 shiftwidth=4:
