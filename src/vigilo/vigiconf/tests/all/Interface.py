# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2006-2011 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

import re # for the detect_snmp function
from vigilo.vigiconf.lib.confclasses.test import Test



class Interface(Test):
    """Check the status of an interface, and graph its throughput"""

    oids = [".1.3.6.1.2.1.25.1.6.0"]

    def add_test(self, host, label, ifname, max=None,
                 errors=True, staticindex=False, warn=None, crit=None,
                 counter32=False, teststate=True ):
        """
        The parameters L{warn} and L{crit} must be tuples in the form of
        strings separated by commas, for example: C{max_in,max_out} (in
        bits/s).

        If warn and crit contain 4 or 6 values, the next values will be applied
        in order to Discards and Errors if they are not None.
        Please note that sub-interfaces (VLANs) do not support SNMP queries
        for the discard and error counters.

        @param host: the Host object to add the test to
        @param label: Label to display
        @param ifname: SNMP name for the interface
        @param max: the maximum bandwidth available through this interface, in
            bits/s
        @param errors: create a graph for interface errors
        @param staticindex: consider the ifname as the static SNMP index instead
            of the interface name. It's not recommanded, but it can be
            necessary as some OS (Windows among others) assign the same name to
            different interfaces.
        @param warn: WARNING threshold. See description for the format.
        @param crit: CRITICAL threshold. See description for the format.
        @param counter32: to use Counter32bits specifically for this interface.
        @param teststate: Used to deactivate the interface state control. (When
            you only need statistics.)

        """
        snmp_oids = {
            # using by default High Capacity (64Bits) COUNTER for in and out
            # http://www.ietf.org/rfc/rfc2233.txt
                "in": ".1.3.6.1.2.1.31.1.1.1.6",
                "out": ".1.3.6.1.2.1.31.1.1.1.10",
                "inDisc": ".1.3.6.1.2.1.2.2.1.13",
                "outDisc": ".1.3.6.1.2.1.2.2.1.19",
                "inErrs": ".1.3.6.1.2.1.2.2.1.14",
                "outErrs": ".1.3.6.1.2.1.2.2.1.20",
                }
        snmp_labels = {
                "in": "Input",
                "out": "Output",
                "inDisc": "Input discards",
                "outDisc": "Output discards",
                "inErrs": "Input errors",
                "outErrs": "Output errors",
                }

        HCIf = host.get_attribute("DisableHighCapacityInterface", True)
        if HCIf is not True or counter32 is not False:
            # using Low Capacity (32Bits) COUNTER for in and out
            snmp_oids["in"]  = ".1.3.6.1.2.1.2.2.1.10"
            snmp_oids["out"] = ".1.3.6.1.2.1.2.2.1.16"

        if "nokia" in host.classes:
            errors = False # Not supported on Nokia hardware
            del snmp_oids["inDisc"]
            del snmp_oids["outDisc"]
            del snmp_oids["inErrs"]
            del snmp_oids["outErrs"]


        if staticindex:
            collector_function = "staticIfOperStatus"
            for snmpname, snmpoid in snmp_oids.iteritems():
                host.add_collector_metro("%s%s" % (snmpname, label),
                                         "directValue", [],
                                         [ "GET/%s.%s" % (snmpoid, ifname) ],
                                         "COUNTER", snmp_labels[snmpname],
                                         max_value=max)
        else:
            collector_function = "ifOperStatus"
            for snmpname, snmpoid in snmp_oids.iteritems():
                host.add_collector_metro("%s%s" % (snmpname, label),
                                         "m_table", [ifname],
                                         [ "WALK/%s" % snmpoid,
                                           "WALK/.1.3.6.1.2.1.2.2.1.2"],
                                         "COUNTER", snmp_labels[snmpname],
                                         max_value=max)

        if teststate is True:
            host.add_collector_service("Interface %s" % label, collector_function,
                [ifname, label, "i"],
                ["WALK/.1.3.6.1.2.1.2.2.1.2", "WALK/.1.3.6.1.2.1.2.2.1.7",
                 "WALK/.1.3.6.1.2.1.2.2.1.8", "WALK/.1.3.6.1.2.1.31.1.1.1.18"],
                weight=self.weight, directives=self.directives)

        host.add_graph("Traffic %s" % label, ["in%s" % label, "out%s" % label],
                    "area-line", "b/s", group="Network interfaces",
                    factors={"in%s" % label: 8, "out%s" % label: 8, },)
        if errors:
            host.add_graph("Errors %s" % label,
                    [ "inErrs%s"%label, "outErrs%s"%label,
                      "inDisc%s"%label, "outDisc%s"%label ],
                    "lines", "packets/s", group="Network interfaces")

        # Supervision service
        if warn and crit:
            warn = warn.replace(" ","").split(",")
            crit = crit.replace(" ","").split(",")
            if warn[0] and crit[0]:
                host.add_metro_service("Traffic in %s"%label, "in"+label,
                                       warn[0], crit[0], 8, weight=self.weight)
            if warn[1] and crit[1]:
                host.add_metro_service("Traffic out %s"%label, "out"+label,
                                       warn[1], crit[1], 8, weight=self.weight)

            if len(warn) >= 4 and len(crit) >= 4:
                if warn[2] and crit[2]:
                    host.add_metro_service("Discards in %s"%label, "inDisc"+label,
                                           warn[2], crit[2], 8, weight=self.weight)
                if warn[3] and crit[3]:
                    host.add_metro_service("Discards out %s"%label, "outDisc"+label,
                                           warn[3], crit[3], 8, weight=self.weight)

                if len(warn) == 6 and len(crit) == 6 and errors:
                    if warn[4] and crit[4]:
                        host.add_metro_service("Errors in %s"%label, "inErrs"+label,
                                               warn[4], crit[4], 8, weight=self.weight)
                    if warn[5] and crit[5]:
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
            # 135 => l2vlan
            # 136 => l3ipvlan
            # 22 => propPointToPointSerial
            # 23 => ppp
            allowed_types = [ "6", "22", "23", "53", "135", "136" ]
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
            label = label.strip()
            label = label.replace("GigabitEthernet", "GE")
            label = label.replace("FastEthernet", "FE")
            # Protection contre les accents (#882)
            ifname = ifname.decode("ascii", "replace"
                          ).encode("ascii", "replace").replace("?", ".")
            try:
                label.decode("ascii")
            except UnicodeDecodeError:
                # On essaye utf8 et latin1, sinon on remplace par des "?".
                try:
                    label = label.decode("utf8")
                except UnicodeDecodeError:
                    try:
                        label = label.decode("iso8859-1")
                    except UnicodeDecodeError:
                        label = label.decode("ascii", "replace")
            tests.append({"label": label, "ifname": ifname})
        return tests

    def detect_attribute_snmp(self, oids):
        """Detection method for the host attribute used in this test.
        See the documentation in the main Test class for details"""
        # Search if HighCapacity Counter must be disabled
        for oid in oids.keys():
            if oid.startswith(".1.3.6.1.2.1.31.1.1.1.6."):
                return None
        return {"DisableHighCapacityInterface": "yes"}


# vim:set expandtab tabstop=4 shiftwidth=4:
