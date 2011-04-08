# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# pylint: disable-msg=C0111,W0212,R0904

import os
import unittest

from vigilo.common.conf import settings

import vigilo.vigiconf.conf as conf
from vigilo.vigiconf.lib.confclasses.host import Host
from vigilo.vigiconf.lib.confclasses.test import TestFactory

from helpers import setup_db, teardown_db


class TestFactoryTest(unittest.TestCase):

    def setUp(self):
        setup_db()
        self.testfactory = TestFactory(confdir=settings["vigiconf"]["confdir"])
        self.host = Host(conf.hostsConf, "dummy", "testserver1", "192.168.1.1", "Servers")

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
        print self.testfactory.path
        self.assertTrue(len(self.testfactory.path) >= 2)
        self.assertEqual(self.testfactory.path[0], default_path)
        self.assertEqual(self.testfactory.path[-1], sysadmin_path)


