# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2006-2018 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.vigiconf.lib.confclasses.test import Test


class Collector(Test):
    """The Collector service"""

    def add_test(self):
        self.add_external_sup_service("Collector", "Collector")


# vim:set expandtab tabstop=4 shiftwidth=4:
