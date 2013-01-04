# -*- coding: utf-8 -*-
# vim:set expandtab tabstop=4 shiftwidth=4:
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2011-2013 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.vigiconf.lib.confclasses.test import Test



class HTTP_url(Test):
    """Check if the HTTP service is up for a given url"""

    def add_test(self, service, port=80, url="/"):
        """
        @param service: Le nom du service à utiliser dans Nagios.
        @param port:    Le port sur lequel le serveur web écoute
                        (80 par défaut).
        @param url:     L'URL à demander au serveur web.
        """
        port = self.as_int(port)

        # remove http://
        if url.startswith("http://"):
            url = url[7:]

        self.add_external_sup_service(
            service, "check_http_url!%d!%s" % (port, url))
        self.add_perfdata_handler(service, 'HTTP-time', 'response time', 'time')
        self.add_graph("HTTP response time", [ 'HTTP-time' ], 'lines', 's')
