# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2011-2018 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.vigiconf.lib.confclasses.test import Test



class LDAPS(Test):
    """Vérifie la disponibilité d'un serveur LDAP en utilisant SSL/TLS"""

    def add_test(self, base, starttls=False):
        """
        @param  base:       Base de recherche dans l'annuaire.
        @type   base:       C{str}
        @param  starttls:   Indique si le mécanisme STARTTLS est utilisé ou non.
        @type   starttls:   C{bool}
        """
        starttls = self.as_bool(starttls)
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
