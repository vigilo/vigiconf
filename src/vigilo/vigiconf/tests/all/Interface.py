# -*- coding: utf-8 -*-

import re # for the detect_snmp function

class Interface(Test):
    """Check the status of an interface, and graph its throughput"""

    oids = [".1.3.6.1.2.1.25.1.6.0"]

    def add_test(self, host, label, ifname, max=None,
                errors=True, staticindex=False, warn=None, crit=None):
        """Arguments:
            host: the Host object to add the test to
            label: Label to display
            ifname: SNMP name for the interface
            max: the maximum bandwidth available through this interface.
            errors: create a graph for interface errors
            staticindex: consider the ifname as the static SNMP index instead
                         of the interface name. It's not recommanded, but it
                         can be necessary as some OS (Windows among others)
                         assign the same name to different interfaces.
            warn: WARNING threshold. See below for the format
            crit: CRITICAL threshold. See below for the format

            warn and crit must be tuples in the form of strings separated by
            commas, for example: max_in,max_out (in bits/s).
            If warn and crit contain 4 or 6 values, the next values will be
            applied in order to Discards and Errors if they are not None.
        """

        if "nokia" in host.classes:
            errors = False # Not supported on Nokia hardware
        snmp_ids = { 10:"in", 16:"out" }
        if errors:
            snmp_ids.update( {13: "inDisc",
                              19: "outDisc",
                              14: "inErrs",
                              20: "outErrs",
                              })

        if staticindex:
            for snmpindex, snmpname in snmp_ids.iteritems():
                host.add_collector_metro("%s%s" % (snmpname, label),
                                         "directValue", [],
                                         [ "GET/.1.3.6.1.2.1.2.2.1.%s.%s" % (snmpindex, ifname) ],
                                         "COUNTER")
            host.add_collector_service("Interface %s" % label, "staticIfOperStatus",
                        [ifname, label, "i"],
                        ["WALK/.1.3.6.1.2.1.2.2.1.2", "WALK/.1.3.6.1.2.1.2.2.1.7",
                         "WALK/.1.3.6.1.2.1.2.2.1.8", "WALK/.1.3.6.1.2.1.31.1.1.1.18"],
                        weight=self.weight, directives=self.directives)
        else:
            for snmpindex, snmpname in snmp_ids.iteritems():
                host.add_collector_metro("%s%s" % (snmpname, label),
                                         "m_table", [ifname],
                                         [ "WALK/.1.3.6.1.2.1.2.2.1.%s" % snmpindex,
                                           "WALK/.1.3.6.1.2.1.2.2.1.2"], "COUNTER")
            host.add_collector_service("Interface %s" % label, "ifOperStatus",
                        [ifname, label, "i"],
                        ["WALK/.1.3.6.1.2.1.2.2.1.2", "WALK/.1.3.6.1.2.1.2.2.1.7",
                         "WALK/.1.3.6.1.2.1.2.2.1.8", "WALK/.1.3.6.1.2.1.31.1.1.1.18"],
                        weight=self.weight, directives=self.directives)

            host.add_graph("Traffic %s" % label, ["in%s" % label, "out%s" % label],
                        "area-line", "b/s", group="Network interfaces",
                        factors={
                            "in%s" % label: 8,
                            "out%s" % label: 8,
                        },
                        max_values={
                            "in%s" % label: max,
                            "out%s" % label: max,
                        },
            )
        if errors:
            host.add_graph("Errors %s" % label, [ "inErrs%s"%label, "outErrs%s"%label,
                                        "inDisc%s"%label, "outDisc%s"%label ], "lines",
                                        "packets/s", group="Network interfaces")
        if ifname != label:
            host.add_trap("%s.interfaces" % host.get("address"), ifname, label)

        # Supervision service
        if warn and crit:
            warn = warn.replace(" ","").split(",")
            crit = crit.replace(" ","").split(",")
            host.add_metro_service("Traffic in %s"%label, "in"+label,
                                   warn[0], crit[0], 8, weight=self.weight)
            host.add_metro_service("Traffic out %s"%label, "out"+label,
                                   warn[1], crit[1], 8, weight=self.weight)
            if len(warn) >= 4 and len(crit) >= 4:
                host.add_metro_service("Discards in %s"%label, "inDisc"+label,
                                       warn[2], crit[2], 8, weight=self.weight)
                host.add_metro_service("Discards out %s"%label, "outDisc"+label,
                                       warn[3], crit[3], 8, weight=self.weight)
                if len(warn) == 6 and len(crit) == 6 and errors:
                    host.add_metro_service("Errors in %s"%label, "inErrs"+label,
                                           warn[4], crit[4], 8, weight=self.weight)
                    host.add_metro_service("Errors out %s"%label, "outErrs"+label,
                                           warn[5], crit[5], 8, weight=self.weight)


    def detect_snmp(self, oids):
        """Detection method, see the documentation in the main Test class"""
        # Find the SNMP ids of interfaces with the right type. Types are in the
        # OID IF-MIB::ifType section
        intfids = []
        for oid in oids.keys():
            # Search IF-MIB::ifType
            if not oid.startswith(".1.3.6.1.2.1.2.2.1.3."):
                continue
            # Select the types
            # 6   => ethernetCsmacd
            # 53  => propVirtual
            # 136 => l3ipvlan
            allowed_types = [ "6", "53", "136" ]
            if oids[oid] not in allowed_types:
                continue
            # Extract the SNMP id
            intfids.append(oid.split(".")[-1])
        tests = []
        for intfid in intfids:
            # SNMP name: use IF-MIB::ifDescr and sanitize it
            ifname = oids[ ".1.3.6.1.2.1.2.2.1.2."+intfid ]
            ifname = re.sub("; .*", "; .*", ifname)
            if ifname == "lo": # Don't monitor the loopback
                continue
            # label: start with ifname and sanitize
            label = ifname
            label = re.sub("; .*", "", label)
            label = label.replace("GigabitEthernet", "GE")
            label = label.replace("FastEthernet", "FE")
            tests.append({"label": label, "ifname": ifname})
        return tests


# vim:set expandtab tabstop=4 shiftwidth=4:
