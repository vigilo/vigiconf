# -*- coding: utf-8 -*-

class RAM(Test):
    """Check the RAM usage for a host"""

    oids = [".1.3.6.1.2.1.25.2.3.1.2"]

    def add_test(self, host, **kw):
        """Arguments:
            host: the Host object to add the test to
            warn: WARNING threshold
            crit: CRITICAL threshold
            **kw: unused (compatibility layer for other RAM tests)
        """
        # These classes have better RAM tests :
        skipclasses = [ "cisco", "windows2000", "rapidcity", "xmperf", "netware" ]
        for skipclass in skipclasses:
            if skipclass in host.classes:
                return # don't use this tests, use the class' test

        # Search for "hrStorageRam" type
        host.add_collector_metro("Used RAM", "m_table_mult", [".1.3.6.1.2.1.25.2.1.2"], 
                    ["WALK/.1.3.6.1.2.1.25.2.3.1.4", "WALK/.1.3.6.1.2.1.25.2.3.1.6",
                    "WALK/.1.3.6.1.2.1.25.2.3.1.2"], "GAUGE")
        host.add_graph("RAM", [ "Used RAM" ], "lines", "bytes", group="Performance")


# vim:set expandtab tabstop=4 shiftwidth=4:
