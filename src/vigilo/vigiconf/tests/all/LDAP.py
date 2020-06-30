# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2011-2020 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from __future__ import unicode_literals

from vigilo.vigiconf.lib.confclasses.validators import arg, String, Integer
from vigilo.vigiconf.lib.confclasses.test import Test
from vigilo.common.gettext import l_


class LDAP(Test):
    """Vérifie la disponibilité d'un serveur LDAP"""

    @arg(
        'base', String,
        l_('Starting point'),
        l_("Starting point for the search inside the directory")
    )
    def add_test(self, base):
        self.add_external_sup_service("LDAP", "check_ldap!%s" % base)
        self.add_perfdata_handler("LDAP", 'LDAP-time', 'response time', 'time')
        self.add_graph("LDAP response time", [ 'LDAP-time' ], 'lines', 's')


# vim:set expandtab tabstop=4 shiftwidth=4:
