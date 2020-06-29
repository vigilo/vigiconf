# -*- coding: utf-8 -*-
# vim:set expandtab tabstop=4 shiftwidth=4:
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2011-2020 CS GROUP – France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from __future__ import unicode_literals

from vigilo.vigiconf.lib.confclasses.validators import arg, String, Port
from vigilo.vigiconf.lib.confclasses.test import Test
from vigilo.common.gettext import l_


class HTTP_url(Test):
    """Check if the HTTP service is up for a given url"""

    @arg(
        'service', String,
        l_('Display name'),
        l_("""
            Name to display in the GUI.

            This setting also controls the name of the service
            created in Nagios (service_description).
        """)
    )
    @arg(
        'port', Port,
        l_('Port number'),
        l_('Port number the web server is listening on')
    )
    @arg(
        'url', String,
        l_('URL'),
        l_("URL to request from the server")
    )
    def add_test(self, service, port=80, url="/"):
        # remove http://
        if url.startswith("http://"):
            url = url[7:]

        self.add_external_sup_service(
            service, "check_http_url!%d!%s" % (port, url))
        self.add_perfdata_handler(service, 'HTTP-time', 'response time', 'time')
        self.add_graph("HTTP response time", [ 'HTTP-time' ], 'lines', 's')
