# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903
# Copyright (C) 2011-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.vigiconf.lib.confclasses.test import Test


class RAID(Test):
    """Check the RAID status of a host"""

    def add_test(self, host):
        """Arguments:
            host:   the Host object to add the test to
        """
        host.add_external_sup_service("RAID", "check_nrpe_1arg!check_raid",
                              weight=self.weight,
                              warning_weight=self.warning_weight,
                              directives=self.directives)


# vim:set expandtab tabstop=4 shiftwidth=4:
