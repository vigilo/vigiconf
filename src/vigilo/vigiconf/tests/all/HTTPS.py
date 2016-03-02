# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2011-2016 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.vigiconf.lib.confclasses.test import Test



class HTTPS(Test):
    """Check if the SSL certificates on the HTTPS server are OK"""

    def add_test(self):
        self.add_external_sup_service("HTTPS", "check_https")


# vim:set expandtab tabstop=4 shiftwidth=4:
