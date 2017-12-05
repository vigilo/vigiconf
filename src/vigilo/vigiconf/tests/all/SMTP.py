# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2017 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.vigiconf.lib.confclasses.test import Test
from vigilo.common.gettext import translate
_ = translate(__name__)


class SMTP(Test):
    """Vérifie la connectivité d'un serveur SMTP"""

    def add_test(self):
        """
        Teste la connectivité d'un serveur SMTP et lève une
        alarme dont la gravité dépend du temps de réponse
        du serveur.
        """

        self.add_external_sup_service("SMTP", "check_smtp")
        self.add_perfdata_handler("SMTP", "SMTP-time", "response time", "time")
        self.add_graph("SMTP response time", ["SMTP-time"], "lines", "s")


# vim:set expandtab tabstop=4 shiftwidth=4:
