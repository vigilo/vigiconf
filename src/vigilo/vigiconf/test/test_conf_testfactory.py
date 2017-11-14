# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# pylint: disable-msg=C0111,W0212,R0904
# Copyright (C) 2006-2018 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>
from __future__ import absolute_import, print_function

import os
import unittest

from vigilo.common.conf import settings

import vigilo.vigiconf.conf as conf
from vigilo.vigiconf.lib.confclasses.host import Host
from vigilo.vigiconf.lib.confclasses.test import TestFactory

from .helpers import setup_db, teardown_db
from vigilo.vigiconf.lib import VigiConfError

from vigilo.common.gettext import translate
_ = translate(__name__)

class TestFactoryTest(unittest.TestCase):

    def setUp(self):
        conf.load_general_conf() # Réinitialisation de la configuration
        setup_db()
        self.testfactory = TestFactory(confdir=settings["vigiconf"]["confdir"])
        self.host = Host(
            conf.hostsConf,
            "dummy",
            "testserver1",
            "192.168.1.1", "Servers",
        )

    def tearDown(self):
        teardown_db()


    def test_get_testnames(self):
        """Test for the get_testname method"""
        testnames = self.testfactory.get_testnames()
        self.assertTrue("UpTime" in testnames, "get_testnames does not work")

    def test_get_hclasses(self):
        """Test for the get_hclasses method"""
        hclasses = self.testfactory.get_hclasses()
        self.assertTrue("all" in hclasses, "get_hclasses does not work")

    def test_list_test_paths(self):
        """
        La liste des chemins des tests doit contenir ceux de VigiConf et ceux de l'admin sys
        """
        default_path = os.path.normpath(os.path.join(
                            os.path.dirname(__file__), "..", "tests"))
        sysadmin_path = os.path.join(settings["vigiconf"]["confdir"], "tests")
        print(self.testfactory.path)
        self.assertTrue(len(self.testfactory.path) >= 2)
        self.assertEqual(self.testfactory.path[0], sysadmin_path)
        self.assertEqual(self.testfactory.path[1], default_path)


class TestFactoryImportsTest(unittest.TestCase):
    def setUp(self):
        conf.load_general_conf() # Réinitialisation de la configuration
        setup_db()
        tests_path = os.path.normpath(os.path.join(
                        os.path.dirname(__file__), "testdata"))
        self.testfactory = TestFactory(confdir=tests_path)
        self.host = Host(
            conf.hostsConf,
            "dummy", "testserver1",
            "192.168.1.1", "Servers",
        )

    def tearDown(self):
        teardown_db()

    def test_import(self):
        """
        Les imports doivent correctement être gérés par la TestFactory.
        """
        print(self.testfactory.path)
        self.testfactory.load_tests()
        testclass = self.testfactory.get_test('imports.Error')
        self.assertNotEqual(None, testclass)
        test = testclass(self.host, None)

        # On ne peut pas utiliser self.assertRaises à cause du rebinding
        # des classes dans TestFactory.
        try:
            test.add_test()
        except VigiConfError as e:
            self.assertEqual(_("Import test was successful"), unicode(e))
        except Exception as e:
            self.fail("Unexpected exception of type %r" % type(e))
        else:
            self.fail("Expected VigiConfError exception")
