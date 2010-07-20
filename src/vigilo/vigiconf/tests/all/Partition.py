# -*- coding: utf-8 -*-

class Partition(Test):
    """Check if a partition is filling up"""

    oids = [".1.3.6.1.2.1.25.2.3.1.3"]

    def add_test(self, host, label, partname, max=None, warn=80, crit=95, percent=True):
        """
        Arguments:
            host:     the Host object to add the test to
            label:    the displayed name for the partition (ex: Data)
            partname: the SNMP name of the partition (ex: /var)
            max:      total size of the partition
            warn:     WARNING threshold
            crit:     CRITICAL threshold
            percent:  if True, the thresholds apply to the percent. If False,
                      they apply to the number of bytes
        """
        host.add_collector_service("Partition %s"%label, "storage",
                    [partname,warn,crit,int(percent)],
                    ["WALK/.1.3.6.1.2.1.25.2.3.1.3", "WALK/.1.3.6.1.2.1.25.2.3.1.4", 
                     "WALK/.1.3.6.1.2.1.25.2.3.1.5", "WALK/.1.3.6.1.2.1.25.2.3.1.6" ],
                    weight=self.weight)
        host.add_collector_metro("%s part"%label, "m_table_mult", [partname],
                    ["WALK/.1.3.6.1.2.1.25.2.3.1.4", "WALK/.1.3.6.1.2.1.25.2.3.1.6",
                     "WALK/.1.3.6.1.2.1.25.2.3.1.3"],'GAUGE', label=label)
        host.add_graph("%s partition usage"%label, [ "%s part"%label ],
            "lines", "bytes", "Storage", max_values={"%s part" % label: max})



    def detect_snmp(self, oids):
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
            if oids[ ".1.3.6.1.2.1.25.2.3.1.5."+partid ] == "0":
                continue
            partids.append(partid)
        tests = []
        for partid in partids:
            # SNMP name: use HOST-RESOURCES-MIB::hrStorageDescr (device)
            partname = oids[ ".1.3.6.1.2.1.25.2.3.1.3."+partid ]
            # sanitize it
            partname = re.sub(" .*", " .*", partname)
            partname = partname.replace(r"\ ", "") # Windows drive letters
            label = self._get_label(partid, oids)
            if not label:
                # No mountpoint found: maybe Windows ? Use partname
                label = oids[ ".1.3.6.1.2.1.25.2.3.1.3."+partid ]
            tests.append({"label": label, "partname": partname})
        return tests

    def _get_label(self, partid, oids):
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
                return label

# vim:set expandtab tabstop=4 shiftwidth=4:
