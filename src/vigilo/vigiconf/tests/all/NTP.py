# -*- coding: utf-8 -*-

class NTP(Test):
    """Check if the NTP service is up"""

    def add_test(self, host):
        """Arguments:
            host: the Host object to add the test to
        """
        host.add_external_sup_service("NTP", "check_ntp", weight=self.weight)


# vim:set expandtab tabstop=4 shiftwidth=4:
