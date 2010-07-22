# -*- coding: utf-8 -*-

class HTTPS(Test):
    """Check if the SSL certificates on the HTTPS server are OK"""

    def add_test(self, host):
        """Arguments:
            host: the Host object to add the test to
        """
        host.add_external_sup_service("HTTPS", "check_https",
                weight=self.weight, directives=self.directives)


# vim:set expandtab tabstop=4 shiftwidth=4:
