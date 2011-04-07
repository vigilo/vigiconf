# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903

from vigilo.vigiconf.lib.confclasses.test import Test



class HTTPS(Test):
    """Check if the SSL certificates on the HTTPS server are OK"""

    def add_test(self, host):
        """Arguments:
            host: the Host object to add the test to
        """
        host.add_external_sup_service("HTTPS", "check_https",
                weight=self.weight, directives=self.directives)


# vim:set expandtab tabstop=4 shiftwidth=4:
