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

