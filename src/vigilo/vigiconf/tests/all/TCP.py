# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2011-2020 CS GROUP – France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from __future__ import unicode_literals

from vigilo.vigiconf.lib.confclasses.validators import arg, String, Port
from vigilo.vigiconf.lib.confclasses.test import Test
from vigilo.common.gettext import l_


class TCP(Test):
    """Check if the requested TCP port is open"""

    @arg(
        'label', String,
        l_('Display name'),
        l_("""
            Name to display in the GUI.

            This settings also controls the name of the service
            created in Nagios (service_description).
        """)
    )
    @arg(
        'port', Port,
        l_('Port number'),
        l_("TCP port to test")
    )
    def add_test(self, port, label=None):
        if not label:
            label = "TCP %d" % port
        self.add_external_sup_service(label, "check_tcp!%d" % port)


# vim:set expandtab tabstop=4 shiftwidth=4:
