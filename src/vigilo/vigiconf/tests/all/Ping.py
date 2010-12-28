# -*- coding: utf-8 -*-

class Ping(Test):
    """Check if a host is up with a ping"""

    def add_test(self, host, warn=(1,5), crit=(5,20)):
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
        host.add_perfdata_handler("Ping", 'Ping-loss', 'pl', 'Loss')
        host.add_perfdata_handler("Ping", 'Ping-RTA', 'rta', 'Round-trip average')
        host.add_graph("Ping", [ 'Ping-RTA', 'Ping-loss' ], 'lines', 'ms , %')

# vim:set expandtab tabstop=4 shiftwidth=4:
