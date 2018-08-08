# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2006-2018 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from __future__ import unicode_literals

import re

from vigilo.vigiconf.lib.confclasses.validators import (
    arg, String, Threshold, Bool, Integer
)
from vigilo.vigiconf.lib.confclasses.test import Test
from vigilo.common.gettext import l_



class Partition(Test):
    """Check if a partition is filling up"""

    oids = [".1.3.6.1.2.1.25.2.3.1.3"]

    @arg(
        'warn', Threshold,
        l_('WARNING threshold'),
        l_("""
            Trigger a WARNING alarm whenever the amount
            of remaining free space is outside the configured threshold.
        """)
    )
    @arg(
        'crit', Threshold,
        l_('CRITICAL threshold'),
        l_("""
            Trigger a CRITICAL alarm whenever the amount
            of remaining free space is outside the configured threshold.
        """)
    )
    @arg(
        'label', String,
        l_('Display name'),
        l_("""
            Name to display in the GUI.

            This setting also controls the name of the service
            created in Nagios (service_description).
        """)
    )
    @arg(
        'partname', String,
        l_('Partition name'),
        l_("SNMP name for the partition (eg. C{/var})")
    )
    @arg(
        'max', Integer(min=0),
        l_('Total size'),
        l_("Total size of the partition (in bytes)")
    )
    @arg(
        'percent', Bool,
        l_('Use percentages'),
        l_("""
            If enabled, the WARNING and CRITICAL thresholds use percentages.
            Otherwise, they represent the minimum free space expected in bytes.
        """)
    )
    def add_test(self, label, partname, max=None, warn=80, crit=95, percent=True):
        self.add_collector_service("Partition %s" % label, "storage",
                    [partname, warn, crit, int(percent)],
                    ["WALK/.1.3.6.1.2.1.25.2.3.1.3",
                     "WALK/.1.3.6.1.2.1.25.2.3.1.4",
                     "WALK/.1.3.6.1.2.1.25.2.3.1.5",
                     "WALK/.1.3.6.1.2.1.25.2.3.1.6" ])
        self.add_collector_metro("%s part" % label, "m_table_mult", [partname],
                    ["WALK/.1.3.6.1.2.1.25.2.3.1.4",
                     "WALK/.1.3.6.1.2.1.25.2.3.1.6",
                     "WALK/.1.3.6.1.2.1.25.2.3.1.3"],
                    'GAUGE', label=label, max_value=max or None)
        self.add_graph("%s partition usage" % label, [ "%s part"%label ],
                       "lines", "bytes", "Storage")


    @classmethod
    def detect_snmp(cls, oids):
        """Detection method, see the documentation in the main Test class"""
        # Find the SNMP ids of partitions with the SNMP type
        # HOST-RESOURCES-TYPES::hrStorageFixedDisk
        partids = []
        for oid in oids.keys():
            # Search HOST-RESOURCES-MIB::hrStorageType
            if not oid.startswith(".1.3.6.1.2.1.25.2.3.1.2."):
                continue
            # Select HOST-RESOURCES-TYPES::hrStorageFixedDisk
            if oids[oid] != ".1.3.6.1.2.1.25.2.1.4":
                continue
            # Extract the SNMP id
            partid = oid.split(".")[-1]
            # If the HOST-RESOURCES-MIB::hrStorageSize is zero, it's a virtual
            # filesystem, skip it
            if oids[ ".1.3.6.1.2.1.25.2.3.1.5." + partid ] == "0":
                continue
            partids.append(partid)
        tests = []
        for partid in partids:
            # SNMP name: use HOST-RESOURCES-MIB::hrStorageDescr (device)
            partname = oids[ ".1.3.6.1.2.1.25.2.3.1.3." + partid ]
            # sanitize it
            partname = re.sub(" .*", " .*", partname)
            partname = partname.replace(r"\ ", "") # Windows drive letters
            label = cls._get_label(partid, oids)
            if not label:
                # No mountpoint found: maybe Windows ? Use partname
                label = oids[ ".1.3.6.1.2.1.25.2.3.1.3." + partid ]
                label = label.replace("\\", "") # Windows drive letters
            tests.append({"label": label, "partname": partname})
        return tests

    @classmethod
    def _get_label(cls, partid, oids):
        """Search HOST-RESOURCES-MIB::hrFSTable for the mountpoint of a
           device ID"""
        for oid in oids.keys():
            # Search HOST-RESOURCES-MIB::hrFSStorageIndex
            if not oid.startswith(".1.3.6.1.2.1.25.3.8.1.7"):
                continue
            if oids[oid] == partid:
                fsid = oid.split(".")[-1]
                # now use HOST-RESOURCES-MIB::hrFSMountPoint
                label = oids[ ".1.3.6.1.2.1.25.3.8.1.2."+fsid ]
                label = label.replace('"', '')
                label = label.replace("\\", "")
                return label

# vim:set expandtab tabstop=4 shiftwidth=4:
