# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2011-2020 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from __future__ import unicode_literals

from vigilo.vigiconf.lib.confclasses.validators import arg, Threshold
from vigilo.vigiconf.lib.confclasses.test import Test
from vigilo.vigiconf.lib import VigiConfError
from vigilo.common.gettext import translate, l_
_ = translate(__name__)



class UpTime(Test):
    """Check the SNMP server's uptime"""

    oids = [".1.3.6.1.2.1.1.3.0"]

    @arg(
        'warn', Threshold,
        l_('WARNING threshold'),
        l_("""
            A WARNING alarm will be generated if the duration (in seconds)
            since the device or SNMP agent's last restart is outside the
            specified threshold.
        """)
    )
    @arg(
        'crit', Threshold,
        l_('CRITICAL threshold'),
        l_("""
            A CRITICAL alarm will be generated if the duration (in seconds)
            since the device or SNMP agent's last restart is outside the
            specified threshold.
        """)
    )
    def add_test(self, warn="900:", crit="400:"):
        self.add_collector_service("UpTime", "sysUpTime", [crit, warn],
                            ["GET/.1.3.6.1.2.1.1.3.0"])
        self.add_collector_metro("sysUpTime", "m_sysUpTime", [],
                            ["GET/.1.3.6.1.2.1.1.3.0"], 'GAUGE', label="UpTime")
        self.add_graph("UpTime", [ "sysUpTime" ], "lines", "days",
                            factors={"sysUpTime": round(1.0/86400, 10)})


# vim:set expandtab tabstop=4 shiftwidth=4:
