# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2011-2020 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from __future__ import unicode_literals

from vigilo.vigiconf.lib.confclasses.validators import arg, String, Bool
from vigilo.vigiconf.lib.confclasses.test import Test
from vigilo.common.gettext import l_


class LDAPS(Test):
    """Vérifie la disponibilité d'un serveur LDAP en utilisant SSL/TLS"""

    @arg(
        'base', String,
        l_('Starting point'),
        l_("Starting point for the search inside the directory")
    )
    @arg(
        'starttls', Bool,
        l_('Use STARTTLS'),
        l_("""
            Specifies how the encrypted session is established.

            When enabled, a plain connection is first established
            and the STARTTLS extension is then used to negotiate
            the encryption.

            Otherwise, an SSL/TLS session is negotiated directly
            as part of the connection process.
        """)
    )
    def add_test(self, base, starttls=False):
        if starttls:
            service = "LDAPS-STARTTLS"
            check = "check_ldaps"
        else:
            service = "LDAPS"
            check = "check_ldap_ssl"

        self.add_external_sup_service(service, "%s!%s" % (check, base))
        self.add_perfdata_handler(service, '%s-time' % service, 'response time', 'time')
        self.add_graph("%s response time" % service, [ '%s-time' % service ], 'lines', 's')


# vim:set expandtab tabstop=4 shiftwidth=4:
