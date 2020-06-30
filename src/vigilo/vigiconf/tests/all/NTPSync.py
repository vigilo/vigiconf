# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2011-2020 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.vigiconf.lib.confclasses.test import Test



class NTPSync(Test):
    """Check if a host's time is synchronized with the NTP server (using NRPE)"""

    def add_test(self):
        self.add_external_sup_service("NTP sync", "check_nrpe_1arg!check_ntp_time")
        self.add_perfdata_handler("NTP sync", 'NTP-offset', 'offset', 'offset')
        self.add_graph("NTP Sync", [ 'NTP-offset' ], 'lines', 's')


# vim:set expandtab tabstop=4 shiftwidth=4:
