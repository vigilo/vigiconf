# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2017-2019 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.vigiconf.lib.confclasses.test import Test
from vigilo.common.gettext import translate
_ = translate(__name__)


class DNS(Test):
    """Test a DNS server's availability"""

    def add_test(self):
        # On passe une chaîne vide en tant que requête,
        # ce qui permet de tester simplement le temps de réponse du serveur,
        # sans faire de suppositions sur les enregistrements qu'il contient.
        self.add_external_sup_service("DNS", "check_dig!''")
        self.add_perfdata_handler("DNS", "DNS-time", "response time", "time")
        self.add_graph("DNS response time", ["DNS-time"], "lines", "s")


# vim:set expandtab tabstop=4 shiftwidth=4:
