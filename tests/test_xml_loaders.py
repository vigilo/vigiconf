#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
loaders test.

 * host groups
 * service groups
 * dependencies
"""

import os, unittest, shutil

from vigilo.vigiconf import loaders

import vigilo.vigiconf.conf as conf
from confutil import reload_conf, setup_db, teardown_db

from vigilo.models import HostGroup, ServiceGroup


class XMLLoadersTest(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        reload_conf()
        setup_db()
        
    def tearDown(self):
        """Call after every test case."""
        teardown_db()

        
    def test_load_hostgroups(self):
        loaders.load_hostgroups('tests/testdata/xsd/hostgroups/ok')
        
        root_group = HostGroup.by_group_name('root_group')
        self.assertTrue(root_group, "root_group created.")
        
        self.assertEquals(len(root_group.children), 3, "root group has 3 children")
        
    def test_load_servicegroups(self):
        loaders.load_servicegroups('tests/testdata/xsd/servicegroups/ok')
        
        root_group = HostGroup.by_group_name('root_group')
        self.assertTrue(root_group, "root_group created.")
        
        self.assertEquals(len(root_group.children), 3, "root group has 3 children")
        
        
