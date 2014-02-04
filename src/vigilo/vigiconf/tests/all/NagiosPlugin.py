# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903
# Copyright (C) 2006-2014 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.vigiconf.lib.confclasses.test import Test


class NagiosPlugin(Test):
    """Test générique pour utiliser un plugin Nagios indépendant"""

    def add_test(self, name, command):
        """
        @param name: Le nom du service dans Nagios (service_description)
        @param command: Le nom de la commande à utiliser (check_command)
        """
        # Service
        self.add_external_sup_service(name, command)
        # TODO: ajouter la métrologie


# vim:set expandtab tabstop=4 shiftwidth=4:
