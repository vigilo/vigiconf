# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221

from vigilo.vigiconf.lib.confclasses.test import Test



class TCP(Test):
    """Check if the requested TCP port is open"""

    def add_test(self, host, port, label=None):
        """Arguments:
            host:  the Host object to add the test to
            port:  the TCP port to test
            label: the label to display
        """
        if label is None:
            label = "TCP %s" % port
        host.add_external_sup_service(label, "check_tcp!%s" % port,
                              weight=self.weight, directives=self.directives)


# vim:set expandtab tabstop=4 shiftwidth=4:
