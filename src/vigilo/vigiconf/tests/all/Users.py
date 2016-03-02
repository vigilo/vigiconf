# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2011-2016 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.vigiconf.lib.confclasses.test import Test



class Users(Test):
    """Check the number of connected users"""

    oids = [".1.3.6.1.2.1.25.1.5.0"]

    def add_test(self, warn=50, crit=100):
        """Arguments:
            warn: WARNING threshold
            crit: CRITICAL threshold
        """
        warn = self.as_int(warn)
        crit = self.as_int(crit)

        self.add_collector_service("Users", "thresholds_OID_simple",
                    [warn, crit, "%d users connected"],
                    ["GET/.1.3.6.1.2.1.25.1.5.0"])
        self.add_collector_metro("Users", "directValue", [],
                    ["GET/.1.3.6.1.2.1.25.1.5.0"], "GAUGE",
                    rra_template="discrete")
        self.add_graph("Users", [ "Users" ], "lines", "users")


# vim:set expandtab tabstop=4 shiftwidth=4:
