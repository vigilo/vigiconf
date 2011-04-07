# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903

from vigilo.vigiconf.lib.confclasses.test import Test



class Ping(Test):
    """Check if a host is up with a ping"""

    def add_test(self, host, warn=(3000,20), crit=(5000,100)):
        """Arguments:
            host: the Host object to add the test to
            warn: the WARNING threshold as a tuple: (round_trip_average, packet_loss_percent)
            crit: the CRITICAL threshold as a tuple: (round_trip_average, packet_loss_percent)
        """
        if type(warn) == str:
            tmp = warn.split(",")
            warn = tmp
        if type(crit) == str:
            tmp = crit.split(",")
            crit = tmp
        host.add_external_sup_service("Ping", "check_ping!%s,%s%%!%s,%s%%" %
                        (warn[0],warn[1],crit[0],crit[1]), weight=self.weight,
                        directives=self.directives)
        host.add_perfdata_handler("Ping", 'Ping-loss', 'Loss', 'pl')
        host.add_perfdata_handler("Ping", 'Ping-RTA', 'Round-trip average', 'rta')
        host.add_graph("Ping", [ 'Ping-RTA', 'Ping-loss' ], 'lines', 'ms , %')

# vim:set expandtab tabstop=4 shiftwidth=4:
