# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2006-2018 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from __future__ import unicode_literals

from vigilo.vigiconf.lib.confclasses.validators import (
    arg, String, Enum, Threshold
)
from vigilo.vigiconf.lib.confclasses.test import Test
from vigilo.common.gettext import l_


class Process(Test):
    """Check the number of instances of a process"""

    oids = [".1.3.6.1.2.1.25.4.2.1.2"]

    @arg('warn', Threshold, l_('WARNING threshold'))
    @arg('crit', Threshold, l_('CRITICAL threshold'))
    @arg(
        'label', String,
        l_('Display name'),
        l_("""
            Name to display in the GUI. Defaults to the process name.

            This settings also controls the name of the service
            created in Nagios (service_description).
        """)
    )
    @arg('processname', String, l_('Process name'))
    @arg('section', Enum({
            'name': l_("Process names"),
            'path': l_("Full executable path"),
            'params': l_("Process parameters"),
        }),
        l_('Section'),
        l_("""
            Section in the SNMP table where the process will be looked for.

            Note: some processes may alter their name during their execution.
            In that case, the new name actually replaces the full
            executable's path.

            Note: on some operating systems, the executable path
            may be truncated (eg. to 15 characters on Linux).
        """)
    )
    def add_test(self, processname, section="name", label=None, warn="", crit="@0"):
        if not label:
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
