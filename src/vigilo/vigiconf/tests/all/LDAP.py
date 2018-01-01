# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2011-2018 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.vigiconf.lib.confclasses.test import Test



class LDAP(Test):
    """Vérifie la disponibilité d'un serveur LDAP"""

    def add_test(self, base):
        """
        @param base: Base de recherche dans l'annuaire.
        @type  base: C{str}
        """
        self.add_external_sup_service("LDAP", "check_ldap!%s" % base)
        self.add_perfdata_handler("LDAP", 'LDAP-time', 'response time', 'time')
        self.add_graph("LDAP response time", [ 'LDAP-time' ], 'lines', 's')


# vim:set expandtab tabstop=4 shiftwidth=4:
