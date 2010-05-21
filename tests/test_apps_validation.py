#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test de la validation des applications
"""
import unittest
import vigilo.vigiconf.conf as conf
from confutil import reload_conf

from vigilo.vigiconf.lib import dispatchmodes

class AppsValidationTest(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        reload_conf()
    
    def test_saveToConfig(self):
        """ test partiel de la validation des applis dans la méthode
            saveToConfig
        """
        # Deploy on the localhost only -> switch to Community Edition
        delattr(conf, "appsGroupsByServer")
        dispatchator = dispatchmodes.getinstance()
        
        dispatchator.saveToConfig()
