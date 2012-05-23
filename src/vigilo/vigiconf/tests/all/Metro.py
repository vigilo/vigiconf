# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2011-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.vigiconf.lib.confclasses.test import Test



class Metro(Test):
    """Set a threshold on metrology values"""

    def add_test(self, servicename, metroname, warn, crit, factor=1):
        """
        Set a threshold on metrology values
        @param servicename: the name of the Nagios service
        @type  servicename: C{str}
        @param metroname: the name of the metrology datasource to test
        @type  metroname: C{str}
        @param warn: the WARNING threshold.
        @type  warn: C{str}
        @param crit: the CRITICAL threshold.
        @type  crit: C{str}
        @param factor: the factor to use, if any
        @type  factor: C{int} or C{float}
        """
        factor = self.as_float(factor)
        self.add_metro_service(servicename, metroname, warn, crit, factor)


# vim:set expandtab tabstop=4 shiftwidth=4:
