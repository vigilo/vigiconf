# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2011-2014 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.vigiconf.lib.confclasses.test import Test



class TCP(Test):
    """Check if the requested TCP port is open"""

    def add_test(self, port, label=None):
        """Arguments:
            port:  the TCP port to test
            label: the label to display
        """
        port = self.as_int(port)
        if label is None:
            label = "TCP %d" % port
        self.add_external_sup_service(label, "check_tcp!%d" % port)


# vim:set expandtab tabstop=4 shiftwidth=4:
