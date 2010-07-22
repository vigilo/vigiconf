# -*- coding: utf-8 -*-

class CPU(Test):
    """Check the CPU usage of a host (service only)"""

    def add_test(self, host, warn=70, crit=90):
        """Arguments:
            host:   the Host object to add the test to
            warn:   WARNING threshold
            crit:   CRITICAL threshold
        """
        host.add_external_sup_service( "Sys CPU",
                    "check_nrpe!check_cpu_args!%s %s" % (warn, crit),
                    weight=self.weight, directives=self.directives)


# vim:set expandtab tabstop=4 shiftwidth=4:
