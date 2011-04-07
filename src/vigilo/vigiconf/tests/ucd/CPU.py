# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903

from vigilo.vigiconf.lib.confclasses.test import Test



class CPU(Test):
    """Check the CPU usage of a host"""

    oids = [".1.3.6.1.4.1.2021.11.55.0"]

    def add_test(self, host, warn=70, crit=90):
        """Arguments:
            host:    the Host object to add the test to
            warn:    WARNING threshold
            crit:    CRITICAL threshold
        """
        baseoid = "GET/.1.3.6.1.4.1.2021.11.5%d.0"
        # don't include System time as it seems to be sum(Wait,Kernel)
        activities = [ ("Kernel",baseoid%5), ("Wait",baseoid%4),
                       ("Interrupt",baseoid%6), ("Nice",baseoid%1),
                       ("User",baseoid%0), ("Idle",baseoid%3) ]

        for activity, oid in activities:
            host.add_collector_metro("CPU %s"%activity, "directValue", [], [ oid ], 'COUNTER')
        host.add_graph("CPU usage (by type)", [ "CPU %s"%a for a,o in activities ],
                       "stacks", "usage (%)", group="Performance")


# vim:set expandtab tabstop=4 shiftwidth=4:
