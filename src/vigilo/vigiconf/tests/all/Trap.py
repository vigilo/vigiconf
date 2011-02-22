# -*- coding: utf-8 -*-

import re # for the detect_snmp function

class Trap(Test):
    """Check the status of an interface, and graph its throughput"""

    def add_test(self, host, label, OID, command, service, address=None, mode="or"):
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
        if mode.lower() not in ["or", "and"]:
            print "Error: Trap mode '%s' unknown" % mode
            print "Error: No snmptt configuration will be generated"
            return
        if address:
            if ";" not in address:
                data["address"] = address
            else:
                data["address"] = []
                for i in address.split(";"):
                    data["address"].append(i.strip())
                data["mode"] = mode.lower()
        host.add_trap(service, OID, data)
