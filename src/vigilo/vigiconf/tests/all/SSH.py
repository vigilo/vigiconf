# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2011-2014 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.vigiconf.lib.confclasses.test import Test



class SSH(Test):
    """Check if the SSH service is up"""

    def add_test(self):
        """
        Teste la présence d'un service SSH opérationnel sur la machine.
        """
        self.add_external_sup_service("SSH", "check_ssh")


# vim:set expandtab tabstop=4 shiftwidth=4:
