# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221

from vigilo.vigiconf.lib.confclasses.test import Test



class HTTP(Test):
    """Check if the HTTP service is up"""

    def add_test(self, host):
        """Arguments:
            host:     the Host object to add the test to
        """
        host.add_external_sup_service("HTTP", "check_http", weight=self.weight,
                                        warning_weight=self.warning_weight,
                                        directives=self.directives)
        host.add_perfdata_handler("HTTP", 'HTTP-time', 'response time', 'time')
        host.add_graph("HTTP response time", [ 'HTTP-time' ], 'lines', 's')


# vim:set expandtab tabstop=4 shiftwidth=4:
