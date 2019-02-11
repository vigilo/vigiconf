# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2006-2019 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

import re # for the detect_snmp function
import string

from vigilo.vigiconf.lib.confclasses.validators import (
    arg, Integer, Bool, Enum, List, String, OrderedDict
)
from vigilo.vigiconf.lib.confclasses.test import Test
from vigilo.vigiconf.lib.exceptions import ParsingError
from vigilo.common.gettext import translate, l_
_ = translate(__name__)


class Interface(Test):
    """Check the status of an interface, and graph its throughput"""

    oids = [".1.3.6.1.2.1.25.1.6.0"]

    @arg(
        'warn', List(types=Integer, min=0, max=6, step=2),
        l_('WARNING thresholds'),
        l_("""
            A list containing either 0, 2, 4 or 6 values,
            representing the thresholds for the WARNING state.

            The thresholds apply (in order) to:
                -   Incoming traffic (in bits/s)
                -   Outgoing traffic (in bits/s)
                -   Discards on incoming traffic
                -   Discards on outgoing traffic
                -   Errors on incoming traffic
                -   Errors on outgoing traffic

            Note: the number of WARNING and CRITICAL thresholds
            must be the same.

            Note: sub-interfaces (VLANs) do not support SNMP requests
            on the discards and errors counters.
        """)
    )
    @arg(
        'crit', List(types=Integer, min=0, max=6, step=2),
        l_('CRITICAL thresholds'),
        l_("""
            A list containing either 0, 2, 4 or 6 values,
            representing the thresholds for the WARNING state.

            The thresholds apply (in order) to:
                -   Incoming traffic (in bits/s)
                -   Outgoing traffic (in bits/s)
                -   Discards on incoming traffic
                -   Discards on outgoing traffic
                -   Errors on incoming traffic
                -   Errors on outgoing traffic

            Note: the number of WARNING and CRITICAL thresholds
            must be the same.

            Note: sub-interfaces (VLANs) do not support SNMP requests
            on the discards and errors counters.
        """)
    )
    @arg('label', String,
        l_('Display name'),
        l_("""
            A short label used to customized the names of the services
            created in relation with the network interface.
        """))
    @arg('staticindex', Bool,
        l_('Use a static index'),
        l_("""
            When true, indicates that the interface name
            actually refers to the interface's static SNMP index.

            This is sometimes necessary as some operating systems
            (eg. Microsoft Windows) may assign the same name to
            several interfaces.
        """)
    )
    @arg('ifname', String,
        l_('Interface name'),
        l_("""
            SNMP name for the interface.
            An index number may be used instead if static indexes are enabled.
        """)
    )
    @arg('max', Integer(min=0), 'Maximum bandwidth',
        l_("Maximum bandwidth available for this interface, in bits/s")
    )
    @arg('teststate', Bool,
        l_('Test state'),
        l_("""
            This setting can be used to disable the interface state check.
            This is useful when you only want to graph usage statistics.
        """)
    )
    @arg('errors', Bool,
        l_('Graph errors'),
        l_("""
            When true, indicates that a graph should be created for errors
            and discards.

            Please note that sub-interfaces (VLANs) do not support
            SNMP queries for the discard and error counters.
        """)
    )
    @arg('counter32', Bool,
        l_('Use 32-bit counters'),
        l_("""
            Query the 32-bit counters instead of the 64-bit ones
            for this interface. This is sometimes necessary on older
            devices where 64-bit interface counters are not available.
        """)
    )
    @arg('admin',
        Enum(OrderedDict((
            ("i", l_("Ignore")),
            ("w", l_("WARNING alarm")),
            ("c", l_("CRITICAL alarm")),
        ))),
        l_('Admin state handling'),
        l_("""
            Indicates how to handle network interfaces which have been
            disabled by an administrator.

            You may either ignore this condition or generate
            a WARNING or CRITICAL alarm.
        """)
    )
    @arg('dormant',
        Enum(OrderedDict((
            ("i", l_("Ignore")),
            ("w", l_("WARNING alarm")),
            ("c", l_("CRITICAL alarm")),
        ))),
        l_('Dormant state handling'),
        l_("""
            Indicates how to handle network interfaces which are seen
            as dormant by the device.

            You may either ignore this condition or generate
            a WARNING or CRITICAL alarm.
        """)
    )
    def add_test(self, label, ifname, max=None,
                 errors=True, staticindex=False, warn=None, crit=None,
                 counter32=False, teststate=True, admin="i", dormant="c" ):
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

        if counter32 :
            # using Low Capacity (32Bits) COUNTER for in and out
            snmp_oids["in"]  = ".1.3.6.1.2.1.2.2.1.10"
            snmp_oids["out"] = ".1.3.6.1.2.1.2.2.1.16"

        if staticindex:
            collector_function = "staticIfOperStatus"
            for snmpname, snmpoid in snmp_oids.iteritems():
                self.add_collector_metro("%s%s" % (snmpname, label),
                                         "directValue", [],
                                         [ "GET/%s.%s" % (snmpoid, ifname) ],
                                         "COUNTER", snmp_labels[snmpname],
                                         max_value=max or None)
        else:
            collector_function = "ifOperStatus"
            for snmpname, snmpoid in snmp_oids.iteritems():
                self.add_collector_metro("%s%s" % (snmpname, label),
                                         "m_table", [ifname],
                                         [ "WALK/%s" % snmpoid,
                                           "WALK/.1.3.6.1.2.1.2.2.1.2"],
                                         "COUNTER", snmp_labels[snmpname],
                                         max_value=max or None)

        if teststate:
            self.add_collector_service("Interface %s" % label, collector_function,
                [ifname, label, admin, dormant],
                ["WALK/.1.3.6.1.2.1.2.2.1.2", "WALK/.1.3.6.1.2.1.2.2.1.7",
                 "WALK/.1.3.6.1.2.1.2.2.1.8", "WALK/.1.3.6.1.2.1.31.1.1.1.18"])

        self.add_graph("Traffic %s" % label, ["in%s" % label, "out%s" % label],
                    "area-line", "b/s", group="Network interfaces",
                    factors={"in%s" % label: 8, "out%s" % label: 8, },)
        if errors:
            self.add_graph("Errors %s" % label,
                    [ "inErrs%s"%label, "outErrs%s"%label,
                      "inDisc%s"%label, "outDisc%s"%label ],
                    "lines", "packets/s", group="Network interfaces")

        # Supervision service
        if warn and crit:
            if warn[0] and crit[0]:
                self.add_metro_service("Traffic in %s"%label, "in"+label,
                                       warn[0], crit[0], 8)
            if warn[1] and crit[1]:
                self.add_metro_service("Traffic out %s"%label, "out"+label,
                                       warn[1], crit[1], 8)

            if len(warn) >= 4 and len(crit) >= 4:
                if warn[2] and crit[2]:
                    self.add_metro_service("Discards in %s"%label, "inDisc"+label,
                                           warn[2], crit[2], 8)
                if warn[3] and crit[3]:
                    self.add_metro_service("Discards out %s"%label, "outDisc"+label,
                                           warn[3], crit[3], 8)

                if len(warn) == 6 and len(crit) == 6 and errors:
                    if warn[4] and crit[4]:
                        self.add_metro_service("Errors in %s"%label, "inErrs"+label,
                                               warn[4], crit[4], 8)
                    if warn[5] and crit[5]:
                        self.add_metro_service("Errors out %s"%label, "outErrs"+label,
                                               warn[5], crit[5], 8)


    @classmethod
    def detect_snmp(cls, oids):
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
            # 7   => iso88023Csmacd
            # 22  => propPointToPointSerial
            # 23  => ppp
            # 53  => propVirtual
            # 135 => l2vlan
            # 136 => l3ipvlan
            allowed_types = [ "6", "7", "22", "23", "53", "135", "136" ]
            if oids[oid] not in allowed_types:
                continue
            # Extract the SNMP id
            intfids.append(oid.split(".")[-1])
        tests = []
        alphanum = string.letters + string.digits
        for intfid in intfids:
            # SNMP name: use IF-MIB::ifDescr and sanitize
            # label: start with ifname
            ifname = oids[ ".1.3.6.1.2.1.2.2.1.2." + intfid ]
            ifname = re.sub("; .*", "; .*", ifname)
            if ifname == "lo": # Don't monitor the loopback
                continue

            # label: start with ifname and sanitize
            label = ifname
            label = re.sub("; .*", "", label)
            label = label.strip()
            label = label.replace("GigabitEthernet", "GE")
            label = label.replace("FastEthernet", "FE")

            # Protection contre les accents et
            # autres caractères spéciaux (#882).
            ifpattern = []
            ifname = ifname.decode('ascii', 'replace'
                          ).encode('ascii', 'replace')

            for c in ifname:
                # Les caractères > 127 sont remplacés par un '?'.
                if c == '?':
                    ifpattern.append('.')
                elif c in alphanum:
                    ifpattern.append(c)
                # Les autres caractères non-alphanumériques sont échappés.
                else:
                    ifpattern.append('\\' + c)
            ifname = ''.join(ifpattern)

            try:
                label = label.decode("ascii")
            except UnicodeDecodeError:
                # On essaye utf8 et latin1, sinon on remplace par des "?".
                try:
                    label = label.decode("utf8")
                except UnicodeDecodeError:
                    try:
                        label = label.decode("iso8859-1")
                    except UnicodeDecodeError:
                        label = label.decode("ascii", "replace")

            counter32 = (".1.3.6.1.2.1.31.1.1.1.6.%s" % intfid) not in oids
            tests.append({
                "label": label,
                "ifname": ifname,
                "counter32": str(counter32),
            })
        return tests

# vim:set expandtab tabstop=4 shiftwidth=4:
