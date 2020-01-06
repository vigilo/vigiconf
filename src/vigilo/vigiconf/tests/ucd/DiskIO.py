# vim:set fileencoding=utf-8 expandtab tabstop=4 shiftwidth=4:
# pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2006-2020 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from __future__ import unicode_literals

from vigilo.vigiconf.lib.confclasses.validators import (
    arg, List, Threshold, String
)
from vigilo.vigiconf.lib.confclasses.test import Test
from vigilo.common.gettext import l_


class DiskIO(Test):
    """Monitor the disks Input/Output"""

    @arg(
        'warn', List(min=0, max=2, types=Threshold),
        l_('WARNING threshold'),
        l_("""
            A list containing up to 2 thresholds for the WARNING state.
            The first threshold applies to reads.
            The second threshold applies to writes.

            Note: the number of WARNING and CRITICAL thresholds
            must be the same.
        """)
    )
    @arg(
        'crit', List(min=0, max=2, types=Threshold),
        l_('CRITICAL threshold'),
        l_("""
            A list containing up to 2 thresholds for the CRITICAL state.
            The first threshold applies to reads.
            The second threshold applies to writes.

            Note: the number of WARNING and CRITICAL thresholds
            must be the same.
        """)
    )
    @arg('diskname', String, l_('Disk name'))
    def add_test(self, diskname="hdisk0", warn=None, crit=None):
        """
        @param diskname: disk name
        @type  diskname: C{str}
        @param warn: tuple containing the thresholds for WARNING status. Ex:
            (limit_reads, limit_writes)
        @type  warn: C{list}
        @param crit: tuple containing the thresholds for CRITICAL status. Ex:
            (limit_reads, limit_writes)
        @type  crit: C{list}
        """
        # Metrology
        self.add_collector_metro("IO Reads", "directValue", [],
                ["GET/.1.3.6.1.4.1.2021.11.58.0"], 'COUNTER')
        self.add_collector_metro("IO Writes", "directValue", [],
                ["GET/.1.3.6.1.4.1.2021.11.57.0"], 'COUNTER')
        self.add_graph("IO", [ "IO Reads", "IO Writes" ], "lines",
                "disk I/O /s", "Performance")

        # Service
        if warn is not None and crit is not None:
            if warn[0] is not None and crit[0] is not None:
                self.add_metro_service("IO Reads", "IO Reads",
                                       warn[0], crit[0])
            if warn[1] is not None and crit[1] is not None:
                self.add_metro_service("IO Writes", "IO Writes",
                                       warn[1], crit[1])
