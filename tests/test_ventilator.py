#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ventilator test
"""


import os, unittest, shutil

import vigilo.vigiconf.conf as conf

from confutil import reload_conf, setup_tmpdir

from vigilo.vigiconf.lib.ventilator import appendHost, getServerToUse, findAServerForEachHost
from vigilo.vigiconf.lib.confclasses.host import Host
from vigilo.vigiconf import generator

class VentilatorTest(unittest.TestCase):
    """Test Ventilator"""
      
    def setUp(self):
        """Call before every test case."""
        # Prepare temporary directory
        self.tmpdir = setup_tmpdir()
        os.mkdir(os.path.join(self.tmpdir, "db"))
        self.basedir = os.path.join(self.tmpdir, "deploy")
        conf.hosttemplatefactory.load_templates()
        reload_conf()
    
    def tearDown(self):
        """Call after every test case."""
        #shutil.rmtree(self.tmpdir)
    
    def test_add_host(self):
        #host = Host(conf.hostsConf, "testserver1", "192.168.1.1", "Servers")
        appendHost('supserver.example.com', 'testserver1')
        s = getServerToUse(['supserver.example.com',], 'testserver1')
        self.assertEquals(s, 'supserver.example.com')
        

if __name__ == '__main__':
    unittest.main()
