# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2006-2016 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.vigiconf.lib.confclasses.test import Test



class Proxy(Test):
    """Check if the HTTP proxy works as expected"""

    def add_test(self, port=8080, url="http://www.google.com", auth=False):
        """Arguments:
            port:  the TCP port to test
            url:   the URL to check
            auth:  use authentication or not
        """
        port = self.as_int(port)
        auth = self.as_bool(auth)

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
