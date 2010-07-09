# -*- coding: utf-8 -*-

class UpTime(Test):
    """Check the SNMP server's uptime"""

    oids = [".1.3.6.1.2.1.1.3.0"]

    def add_test(self, host):
        host.add_collector_service("UpTime", "sysUpTime", [],
                            ["GET/.1.3.6.1.2.1.1.3.0"], weight=self.weight)
        host.add_collector_metro("sysUpTime", "m_sysUpTime", [],
                            ["GET/.1.3.6.1.2.1.1.3.0"], 'GAUGE', label="UpTime")
        host.add_graph("UpTime", [ "sysUpTime" ], "lines", "jours", 
                            factors={"sysUpTime": float(1)/86400})


# vim:set expandtab tabstop=4 shiftwidth=4:
