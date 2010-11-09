# -*- coding: utf-8 -*-

import re # for the detect_snmp function

class Trap(Test):
    """Check the status of an interface, and graph its throughput"""

    def add_test(self, host, label, OID, command, service, address=None):
        """Arguments:
            host: the Host object to add the test to
            label: Label to display (use for EVENT name in snmptt conf)
            OID: SNMP Trad OID
            command: path to script
            address: optional IP address. Default one is taken from the host tag
        """
        hostname = host.hosts.keys()[0]
        data = {}
        data["command"] = command
        data["service"] = service
        data["label"] = label
        if address:
            data["address"] = address
        host.add_trap(service, OID, data)
