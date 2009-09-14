# -*- coding: utf-8 -*-

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
        host.add_external_sup_service(label, "check_tcp!%s" % port)


# vim:set expandtab tabstop=4 shiftwidth=4:
