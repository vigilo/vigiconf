# -*- coding: utf-8 -*-

class HTTP(Test):
    """Check if the HTTP service is up"""

    def add_test(self, host):
        """Arguments:
            host:     the Host object to add the test to
        """
        host.add_external_sup_service("HTTP", "check_http", weight=self.weight,
                                        directives=self.directives)
        host.add_perfdata_handler("HTTP", 'HTTP-time', 'response time', 'time')
        host.add_graph("HTTP response time", [ 'HTTP-time' ], 'lines', 's')


# vim:set expandtab tabstop=4 shiftwidth=4:
