# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2006-2013 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.vigiconf.lib.confclasses.test import Test



class Process(Test):
    """Check the number of instances of a process"""

    oids = [".1.3.6.1.2.1.25.4.2.1.2"]

    def add_test(self, processname, section="name", label=None, warn="", crit="@0"):
        """
        @param processname: the name of the process
        @param section: the section to search in the SNMP table
        @param label:   the label to display
        @param warn:    WARNING threshold
        @param crit:    CRITICAL threshold
        """
        if label is None:
            label = processname
        oids = {"name": ".1.3.6.1.2.1.25.4.2.1.2",
                "path": ".1.3.6.1.2.1.25.4.2.1.4",
                "params": ".1.3.6.1.2.1.25.4.2.1.5",
                }
        self.add_collector_service("Process %s"%label, "walk_grep_count",
                [processname, warn, crit, "%%d instances of %s found" % label],
                [ "WALK/%s" % oids[section] ])
        self.add_collector_metro(label, "m_walk_grep_count", [processname],
                [ "WALK/%s" % oids[section] ], "GAUGE", rra_template="discrete")
        self.add_graph("%s process(es)" % label, [ label ], "lines",
                    "process(es)", group="Processes")


    @classmethod
    def detect_snmp(cls, walk):
        """Disable automatic detection: we need a process name anyway"""
        return None

# vim:set expandtab tabstop=4 shiftwidth=4:
