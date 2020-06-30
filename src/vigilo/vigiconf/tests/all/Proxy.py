# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2006-2020 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from __future__ import unicode_literals

from vigilo.vigiconf.lib.confclasses.validators import arg, String, Port, Bool
from vigilo.vigiconf.lib.confclasses.test import Test
from vigilo.common.gettext import l_


class Proxy(Test):
    """Check if the HTTP proxy works as expected"""

    @arg(
        'port', Port,
        l_('Port number'),
        l_("TCP port used by the HTTP proxy")
    )
    @arg('url', String, l_('URL to check'))
    @arg('auth', Bool, l_('Use authentication'))
    def add_test(self, port=8080, url="http://www.google.com", auth=False):
        if url.startswith("http://"):
            if auth:
                checkname = "check_proxy_auth"
            else:
                checkname = "check_proxy_noauth"
            url = url[7:] # remove http://
        elif url.startswith("https://"):
            if auth:
                checkname = "check_proxy_ssl_auth"
            else:
                checkname = "check_proxy_ssl"
        self.add_external_sup_service( "Proxy %s" % url,
                    "%s!%s!%s" % (checkname,port,url))


# vim:set expandtab tabstop=4 shiftwidth=4:
