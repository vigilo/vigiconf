# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903

from vigilo.vigiconf.lib.confclasses.test import Test


class CPU(Test):
    """Check the CPU usage of a host (service only)"""

    def add_test(self, host, warn=70, crit=90):
        """Arguments:
            host:   the Host object to add the test to
            warn:   WARNING threshold
            crit:   CRITICAL threshold
        """
        check_cpu_perf_data = True
        if "ucd" in host.classes:
            # ucd donne des informations de métrologie plus complètes.
            check_cpu_perf_data = False

        host.add_external_sup_service( "Sys CPU",
                    "check_nrpe!check_cpu_args!%s %s %d" %
                        (warn, crit, check_cpu_perf_data),
                    weight=self.weight, warning_weight=self.warning_weight,
                    directives=self.directives)

        if check_cpu_perf_data:
            activities = ('User', 'Kernel', 'Idle', 'Wait')
            for activity in activities:
                host.add_perfdata_handler(
                    "Sys CPU",
                    'CPU %s' % activity,
                    'CPU %s' % activity,
                    activity,
                    'GAUGE')
            host.add_graph("CPU usage (by type)",
                           [ "CPU %s" % a for a in activities ],
                           "stacks", "usage (%)", group="Performance")

        # Dans le cas contraire, ucd ajoutera lui-même le graphe,
        # avec des indicateurs plus granulaires.


# vim:set expandtab tabstop=4 shiftwidth=4:
