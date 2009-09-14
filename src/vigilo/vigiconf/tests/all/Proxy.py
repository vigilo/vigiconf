# -*- coding: utf-8 -*-

class Proxy(Test):
    """Check if the HTTP proxy works as expected"""

    def add_test(self, host, port=8080, url="http://www.google.com", auth=False):
        """Arguments:
            host:  the Host object to add the test to
            port:  the TCP port to test
            url:   the URL to check
            auth:  use authentication or not
        """
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
        host.add_external_sup_service( "Proxy %s"%url,
                    "%s!%s!%s" % (checkname,port,url) )


# vim:set expandtab tabstop=4 shiftwidth=4:
