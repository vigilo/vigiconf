#!/usr/bin/env python

import os
import unittest

from vigilo.common.conf import settings
import vigilo.vigiconf.conf as conf
from vigilo.vigiconf.lib.confclasses.host import Host

from helpers import setup_db, teardown_db
#pylint: disable-msg=C0111


class TestFactory(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        setup_db()
        self.host = Host(conf.hostsConf, "dummy", "testserver1", "192.168.1.1", "Servers")

    def tearDown(self):
        """Call after every test case."""
        conf.hostfactory.hosts = {}
        conf.hostsConf = conf.hostfactory.hosts
        teardown_db()


    def test_get_testnames(self):
        """Test for the get_testname method"""
        testnames = conf.testfactory.get_testnames()
        assert "UpTime" in testnames, \
                "get_testnames does not work"

    def test_get_hclasses(self):
        """Test for the get_hclasses method"""
        hclasses = conf.testfactory.get_hclasses()
        assert "all" in hclasses, "get_hclasses does not work"

    def test_list_test_paths(self):
        """
        La liste des chemins des tests doit contenir ceux de VigiConf et ceux de l'admin sys
        """
        default_path = os.path.normpath(os.path.join(
                            os.path.dirname(__file__), "..", "tests"))
        sysadmin_path = os.path.join(settings["vigiconf"]["confdir"], "tests")
        print conf.testfactory.path
        self.assertTrue(len(conf.testfactory.path) >= 2)
        self.assertEqual(conf.testfactory.path[0], default_path)
        self.assertEqual(conf.testfactory.path[-1], sysadmin_path)


# vim:set expandtab tabstop=4 shiftwidth=4:
