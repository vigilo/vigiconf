# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# pylint: disable-msg=C0111,W0212,R0904
# Copyright (C) 2011-2020 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>
from __future__ import absolute_import, print_function

import os
from vigilo.vigiconf.applications.collector import Collector
from .helpers import GeneratorBaseTestCase

class CollectorGeneratorTestCase(GeneratorBaseTestCase):

    def _get_apps(self):
        return {"collector": Collector()}

    def test_basic(self):
        """Collector: fonctionnement nominal"""
        test_list = self.testfactory.get_test("all.Interface")
        self.host.add_tests(test_list, {"label": u"eth0", "ifname": u"eth0"})
        self._generate()
        self._validate()

    def test_unicode(self):
        """Collector: caractères unicode"""
        test_list = self.testfactory.get_test("all.Interface")
        self.host.add_tests(test_list, {"label": u"aàeéècç",
                                        "ifname": u"aàeéècç"})
        self._generate()
        self._validate()
        cfgfile = os.path.join(self.basedir, "localhost", "collector",
                               "testserver1.pm")
        cfg = open(cfgfile).read()
        print(cfg)
        self.assertFalse("\\" in cfg)
