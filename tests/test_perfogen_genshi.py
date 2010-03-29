#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test performances du moteur de génération basé sur Genshi

comparaison portant sur le générateur connector-metro

"""
import os, shutil
import unittest
import time

from confutil import reload_conf, setup_tmpdir

import vigilo.vigiconf.generator as generator
from vigilo.vigiconf.generators import GeneratorManager
from vigilo.vigiconf.lib.validator import Validator

from confutil import create_vigiloserver

import vigilo.vigiconf.conf as conf

class GenshiGenerationTest(unittest.TestCase):
    
    expand_factor = 100
    
    def setUp(self):
        reload_conf()
        # Prepare temporary directory
        self.tmpdir = setup_tmpdir()
        self.basedir = os.path.join(self.tmpdir, "deploy")
        
        self.mapping = generator.getventilation()
        # expansion for profiling
        for i in range(1, self.expand_factor):
            key0 = self.mapping.keys()[0]
            key = key0 + str(i)
            conf.hostsConf[key] = conf.hostsConf[key0]
            self.mapping[key] = self.mapping[key0]
            n = i % 3
            if not n: self.mapping[key]['connector-metro'] = self.mapping[key0]['connector-metro'] + str(n+1)
        
        self.validator = Validator(self.mapping)
        
        self.manager = GeneratorManager()

    def tearDown(self):
        """Call after every test case."""
        shutil.rmtree(self.tmpdir)       
    
    def test_run_tpl(self):
        classes =  list(self.manager.genclasses)
        for cl in classes:
            if cl.__name__ == 'ConnectorMetroTpl':
                self.manager.genclasses = [cl, ]
                break
        self.assertEquals(len(self.manager.genclasses), 1)
        
        self.manager.generate(self.basedir, self.mapping, self.validator)
    
    def test_run_genshi(self):
        classes =  list(self.manager.genclasses)
        for cl in classes:
            if cl.__name__ == 'ConnectorMetroView':
                self.manager.genclasses = [cl, ]
                break
        self.assertEquals(len(self.manager.genclasses), 1)
        
        t = time.time()
        self.manager.generate(self.basedir, self.mapping, self.validator)
        dt = time.time() - t
        os.system("echo %f > time_genshi.txt" % dt)
        


