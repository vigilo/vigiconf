# -*- coding: utf-8 -*-

class Process(Test):
    """Check the number of instances of a process"""

    oids = [".1.3.6.1.2.1.25.4.2.1.2"]

    def add_test(self, host, processname, section="name", label=None, warn="", crit="@0"):
        """
        Arguments:
            host:    the Host object to add the test to
            processname: the name of the process
            section: the section to search in the SNMP table
            label:   the label to display
            warn:    WARNING threshold
            crit:    CRITICAL threshold
        """
        if label is None:
            label = processname
        oids = {"name": ".1.3.6.1.2.1.25.4.2.1.2",
                "path": ".1.3.6.1.2.1.25.4.2.1.4",
                "params": ".1.3.6.1.2.1.25.4.2.1.5",
                }
        host.add_collector_service("Process %s"%label, "walk_grep_count",
                [processname, warn, crit, "%%d instances of %s found" % label], 
                [ "WALK/%s" % oids[section] ])
        host.add_collector_metro(label, "m_walk_grep_count", [processname], 
                [ "WALK/%s" % oids[section] ], "GAUGE")
        host.add_graph("%s process(es)" % label, [ "label" ], "lines",
                    "process(es)", group="Processes")


    def detect_snmp(self, walk):
        """Disable automatic detection: we need a process name anyway"""
        return None

# vim:set expandtab tabstop=4 shiftwidth=4:
