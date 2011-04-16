# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221

from vigilo.vigiconf.lib.confclasses.test import Test



class NTP(Test):
    """Check if the NTP service is up"""

    def add_test(self, host):
        """Arguments:
            host: the Host object to add the test to
        """
        host.add_external_sup_service("NTP", "check_ntp", weight=self.weight,
                                        directives=self.directives)


# vim:set expandtab tabstop=4 shiftwidth=4:
