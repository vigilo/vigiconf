# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2011-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.vigiconf.lib.confclasses.test import Test



class UpTime(Test):
    """Check the SNMP server's uptime"""

    oids = [".1.3.6.1.2.1.1.3.0"]

    def add_test(self, host):
        host.add_collector_service("UpTime", "sysUpTime", [],
                            ["GET/.1.3.6.1.2.1.1.3.0"], weight=self.weight,
                            warning_weight=self.warning_weight,
                            directives=self.directives)
        host.add_collector_metro("sysUpTime", "m_sysUpTime", [],
                            ["GET/.1.3.6.1.2.1.1.3.0"], 'GAUGE', label="UpTime")
        host.add_graph("UpTime", [ "sysUpTime" ], "lines", "jours",
                            factors={"sysUpTime": round(1.0/86400, 10)})


# vim:set expandtab tabstop=4 shiftwidth=4:
