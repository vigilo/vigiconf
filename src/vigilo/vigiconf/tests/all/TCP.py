# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2011-2018 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.vigiconf.lib.confclasses.test import Test



class TCP(Test):
    """Check if the requested TCP port is open"""

    def add_test(self, port, label=None):
        """
        @param port:  TCP port to test
        @type  port:  C{int}
        @param label: Service name
        @type  label: C{str}
        """
        port = self.as_int(port)
        if label is None:
            label = "TCP %d" % port
        self.add_external_sup_service(label, "check_tcp!%d" % port)


# vim:set expandtab tabstop=4 shiftwidth=4:
