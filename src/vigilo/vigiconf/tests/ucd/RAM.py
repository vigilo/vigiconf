# vim:set fileencoding=utf-8 expandtab tabstop=4 shiftwidth=4:
# pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221

from vigilo.vigiconf.lib.confclasses.test import Test


class RAM(Test):
    """Check the RAM usage of a host"""
    #UCD-SNMP-MIB::memTotalSwap.0
    #.1.3.6.1.4.1.2021.4.3.0
    #UCD-SNMP-MIB::memAvailSwap.0
    #.1.3.6.1.4.1.2021.4.4.0
    #UCD-SNMP-MIB::memTotalReal.0
    #.1.3.6.1.4.1.2021.4.5.0
    #UCD-SNMP-MIB::memAvailReal.0
    #.1.3.6.1.4.1.2021.4.6.0

    oids = [".1.3.6.1.4.1.2021.4.3.0",
            ".1.3.6.1.4.1.2021.4.4.0",
            ".1.3.6.1.4.1.2021.4.5.0",
            ".1.3.6.1.4.1.2021.4.6.0"]

    def add_test(self, host, warn=80, crit=90):
        """
        @param host: the Host object to add the test to
        @param warn: WARNING threshold
        @param crit: CRITICAL threshold
        """

        host.add_collector_metro("Total memory Swap", "directValue", [],
                [ "GET/.1.3.6.1.4.1.2021.4.3.0" ], "GAUGE")
        host.add_collector_metro("Avail memory Swap", "directValue", [],
                [ "GET/.1.3.6.1.4.1.2021.4.4.0" ], "GAUGE")
        host.add_graph("RAM usage (swap)",
                [ "Avail memory Swap", "Total memory Swap" ],
                "stacks", "bytes", group="Performance", last_is_max=True,
                factors={"Total memory Swap": 1024,
                         "Avail memory Swap": 1024})

        host.add_collector_metro("Total memory Real", "directValue", [],
                [ "GET/.1.3.6.1.4.1.2021.4.5.0" ], "GAUGE")
        host.add_collector_metro("Avail memory Real", "directValue", [],
                [ "GET/.1.3.6.1.4.1.2021.4.6.0" ], "GAUGE")
        host.add_graph("RAM usage (Real)",
                ["Avail memory Real", "Total memory Real" ],
                "stacks", "bytes", group="Performance", last_is_max=True,
                factors={"Total memory Real": 1024,
                         "Avail memory Real": 1024})

