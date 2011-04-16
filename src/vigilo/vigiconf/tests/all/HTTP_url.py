# -*- coding: utf-8 -*-
# vim:set expandtab tabstop=4 shiftwidth=4:
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221

from vigilo.vigiconf.lib.confclasses.test import Test



class HTTP_url(Test):
    """Check if the HTTP service is up for a given url"""

    def add_test(self, host, service, port=80, url="/"):
        """Arguments:
            host:    the Host object to add the test to
            service: the name of the service to be used in Nagios
            port:    the TCP port to test
            url:     the URL to check
        """

        # remove http://
        if url.startswith("http://"):
            url = url[7:]

        host.add_external_sup_service(service, "check_http_url!%s!%s" %
            (port, url), weight=self.weight, directives=self.directives)

        host.add_perfdata_handler(service, 'HTTP-time', 'response time', 'time')
        host.add_graph("HTTP response time", [ 'HTTP-time' ], 'lines', 's')

