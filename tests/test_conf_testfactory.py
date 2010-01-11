#!/usr/bin/env python
import sys
import unittest

import vigilo.vigiconf.conf as conf
from vigilo.vigiconf.lib.confclasses.host import Host

from confutil import reload_conf


class TestFactory(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        reload_conf()
        self.host = Host(conf.hostsConf, "testserver1", "192.168.1.1", "Servers")

    def tearDown(self):
        """Call after every test case."""
        pass


    def test_get_testnames(self):
        """Test for the get_testname method"""
        testnames = conf.testfactory.get_testnames()
        assert "UpTime" in testnames, \
                "get_testnames does not work"

    def test_get_hclasses(self):
        """Test for the get_testname method"""
        hclasses = conf.testfactory.get_hclasses()
        assert "all" in hclasses, "get_hclasses does not work"



# vim:set expandtab tabstop=4 shiftwidth=4:
