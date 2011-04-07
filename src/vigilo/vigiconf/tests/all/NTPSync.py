# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903

from vigilo.vigiconf.lib.confclasses.test import Test



class NTPSync(Test):
    """Check if a host's time is synchronized with the NTP server (uses NRPE)"""

    def add_test(self, host):
        """Arguments:
            host:     the Host object to add the test to
        """
        host.add_external_sup_service("NTP sync", "check_nrpe_1arg!check_ntp",
                              weight=self.weight, directives=self.directives)
        host.add_perfdata_handler("NTP sync", 'NTP-offset', 'offset', 'offset')
        host.add_graph("NTP Sync", [ 'NTP-offset' ], 'lines', 's')


# vim:set expandtab tabstop=4 shiftwidth=4:
