# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2006-2015 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

import re

from vigilo.vigiconf.lib.confclasses.test import Test



class Partition(Test):
    """Check if a partition is filling up"""

    oids = [".1.3.6.1.2.1.25.2.3.1.3"]

    def add_test(self, label, partname, max=None, warn=80, crit=95, percent=True):
        """
        @param label:    the displayed name for the partition (ex: C{Data})
        @param partname: the SNMP name of the partition (ex: C{/var})
        @param max:      total size of the partition
        @param warn:     WARNING threshold
        @param crit:     CRITICAL threshold
        @param percent:  if True, the thresholds apply to the percent. If
            C{False}, they apply to the number of bytes
        """
        warn = self.as_float(warn)
        crit = self.as_float(crit)
        percent = self.as_bool(percent)

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
                    'GAUGE', label=label, max_value=max)
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
