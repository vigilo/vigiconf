#!/usr/bin/env python
import sys
import unittest

import conf
from lib.confclasses.host import Host

from . import reload_conf


class TestFactory(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        reload_conf()
        self.host = Host("testserver1", "192.168.1.1", "Servers")

    def tearDown(self):
        """Call after every test case."""
        pass


    def test_get_testnames(self):
        """Test for the get_testname method"""
        testnames = self.host.get_testnames()
        assert "UpTime" in testnames, \
                "get_testnames does not work"

    def test_get_hclasses(self):
        """Test for the get_testname method"""
        hclasses = conf.testfactory.get_hclasses()
        assert "all" in hclasses, "get_hclasses does not work"



# vim:set expandtab tabstop=4 shiftwidth=4:
