# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2011-2019 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from __future__ import unicode_literals

from vigilo.vigiconf.lib.confclasses.validators import (
    arg, String, Threshold, Float
)
from vigilo.vigiconf.lib.confclasses.test import Test
from vigilo.common.gettext import l_


class Metro(Test):
    """Set a threshold on metrology values"""

    @arg('warn', Threshold, l_('WARNING threshold'))
    @arg('crit', Threshold, l_('CRITICAL threshold'))
    @arg(
        'servicename', String,
        l_('Display name'),
        l_("""
            Name to display in the GUI.

            This setting also controls the name of the service
            created in Nagios (service_description).
        """)
    )
    @arg(
        'metroname', String,
        l_('Metric'),
        l_("Name of the metrology metric whose value must be tested")
    )
    @arg(
        'factor', Float,
        l_('Factor'),
        l_("Factor to apply to the raw value before the test")
    )
    def add_test(self, servicename, metroname, warn, crit, factor=1):
        """
        Set a threshold on metrology values
        """
        self.add_metro_service(servicename, metroname, warn, crit, factor)


# vim:set expandtab tabstop=4 shiftwidth=4:
