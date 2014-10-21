# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2011-2014 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.vigiconf.lib.confclasses.test import Test
import warnings
from vigilo.common.gettext import translate
_ = translate(__name__)



class NTP(Test):
    """Check if the NTP service is up"""

    def add_test(self, **kwargs):
        """Arguments:
        @param warn:    WARNING threshold in milliseconds.
        @type warn:     C{int}
        @param crit:    CRITICAL threshold in milliseconds.
        @type crit:     C{int}
        """
        skipclasses = [ "spectracom_netclock", "spectracom_securesync",
                "windows" ]
        for skipclass in skipclasses:
            if skipclass in self.host.classes:
                return
        warnings.warn(DeprecationWarning(_(
            "Test NTP has been deprecated. Please use NagiosPlugin instead")
            ).encode('utf-8'))

        self.add_external_sup_service("NTP", "check_ntp_ntpq")


# vim:set expandtab tabstop=4 shiftwidth=4:
