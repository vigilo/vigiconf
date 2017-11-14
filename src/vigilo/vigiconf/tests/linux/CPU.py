# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903
# Copyright (C) 2011-2018 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.vigiconf.lib.confclasses.test import Test


class CPU(Test):
    """Check the CPU usage of a host (service only)"""

    def add_test(self, warn=70, crit=90):
        """
        @param warn: WARNING threshold
        @type  warn: C{float}
        @param crit: CRITICAL threshold
        @type  crit: C{float}
        """
        warn = self.as_float(warn)
        crit = self.as_float(crit)

        self.add_external_sup_service( "Sys CPU",
                    "check_nrpe!check_cpu_args!%s %s %d" %
                    (warn, crit, True) )

        activities = ('User', 'Kernel', 'Idle', 'Wait')
        for activity in activities:
            self.add_perfdata_handler(
                "Sys CPU",
                'CPU %s' % activity,
                'CPU %s' % activity,
                activity,
                'GAUGE')
        self.add_graph("CPU usage (by type)",
                       [ "CPU %s" % a for a in activities ],
                       "stacks", "usage (%)", group="Performance")

# vim:set expandtab tabstop=4 shiftwidth=4:
