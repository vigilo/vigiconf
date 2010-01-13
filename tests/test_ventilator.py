#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ventilator test
"""


import os, unittest, shutil

import vigilo.vigiconf.conf as conf

from confutil import reload_conf, setup_tmpdir

from vigilo.vigiconf.lib.ventilator import appendHost, getServerToUse, findAServerForEachHost
from vigilo.vigiconf import generator
from vigilo.vigiconf import dbexportator

from vigilo.models.session import DBSession
from vigilo.models import Host

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
        print conf
    
    def tearDown(self):
        """Call after every test case."""
        #shutil.rmtree(self.tmpdir)
    
    def test_add_host(self):
        #host = Host(conf.hostsConf, "testserver1", "192.168.1.1", "Servers")
        appendHost(u'supserver.example.com', u'testserver1')
        s = getServerToUse([u'supserver.example.com',], u'testserver1')
        self.assertEquals(s, u'supserver.example.com')
    
    def test_localventilation_db(self):
        ventilation = generator.get_local_ventilation()
        
        # need locahost in db
        host = Host(
            name=u'localhost',
            checkhostcmd=u'halt -f',
            snmpcommunity=u'public',
            description=u'My Host',
            hosttpl=u'template',
            mainip=u'127.0.0.1',
            snmpport=u'1234',
            weight=42,
        )
        DBSession.add(host)
        DBSession.flush()
        
        #need apps in DB
        dbexportator.update_apps_db()
        
        dbexportator.export_ventilation_DB(ventilation)
        
        

if __name__ == '__main__':
    unittest.main()
