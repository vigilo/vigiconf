# -*- coding: utf-8 -*-

class Ping(Test):
    """Check if a host is up with a ping"""

    def add_test(self, host, warn=(1,5), crit=(5,20)):
        """Arguments:
            host: the Host object to add the test to
            warn: the WARNING threshold as a tuple: (round_trip_average, packet_loss_percent)
            crit: the CRITICAL threshold as a tuple: (round_trip_average, packet_loss_percent)
        """
        host.add_external_sup_service("Ping", "check_ping!%s,%s%%!%s,%s%%" %
                        (warn[0],warn[1],crit[0],crit[1]), weight=self.weight,
                        directives=self.directives)
        # TODO: add a perfdata_handler
        #PING OK -  Paquets perdus = 0%, RTA = 0.61 ms|rta=0.614000ms;1.000000;2.000000;0.000000 pl=0%;5;50;0


# vim:set expandtab tabstop=4 shiftwidth=4:
