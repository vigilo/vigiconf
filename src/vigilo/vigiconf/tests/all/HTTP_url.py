# -*- coding: utf-8 -*-
# vim:set expandtab tabstop=4 shiftwidth=4:
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2011-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.vigiconf.lib.confclasses.test import Test



class HTTP_url(Test):
    """Check if the HTTP service is up for a given url"""

    def add_test(self, host, service, port=80, url="/"):
        """Arguments:
            service: the name of the service to be used in Nagios
            port:    the TCP port to test
            url:     the URL to check
        """

        # remove http://
        if url.startswith("http://"):
            url = url[7:]

        self.add_external_sup_service(
            service, "check_http_url!%s!%s" % (port, url))
        self.add_perfdata_handler(service, 'HTTP-time', 'response time', 'time')
        self.add_graph("HTTP response time", [ 'HTTP-time' ], 'lines', 's')
