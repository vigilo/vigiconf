# -*- coding: utf-8 -*-

class DiskIO(Test):
    """Monitor the disks Input/Output"""

    def add_test(self, host, diskname="hdisk0", warn=None, crit=None):
        """Arguments:
        diskname: disk name. Default: hdisk0
        warn: tuple containing the thresholds for WARNING status. Ex: (limit_reads, limit_writes)
        crit: tuple containing the thresholds for CRITICAL status. Ex: (limit_reads, limit_writes)
        """
        # Metrology
        host.add_collector_metro("IO Reads","directValue",[],
                ["GET/.1.3.6.1.4.1.2021.11.58.0"],'COUNTER')
        host.add_collector_metro("IO Writes","directValue",[],
                ["GET/.1.3.6.1.4.1.2021.11.57.0"],'COUNTER')
        host.add_graph("IO", [ "IO Reads","IO Writes" ], "lines",
                "disk I/O /s", "Performance")
        # Service
        if warn is not None and crit is not None:
            if warn[0] is not None and crit[0] is not None:
                host.add_metro_service("IO Reads","IO Reads",warn[0],crit[0],
                        weight=self.weight)
            if warn[1] is not None and crit[1] is not None:
                host.add_metro_service("IO Writes","IO Writes",warn[1],crit[1],
                        weight=self.weight)


# vim:set expandtab tabstop=4 shiftwidth=4:
