#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ventilator test
"""


import os, unittest, shutil

import vigilo.vigiconf.conf as conf

from confutil import reload_conf, setup_tmpdir, setup_db, teardown_db

from vigilo.vigiconf.lib.ventilator import appendHost, getServerToUse, findAServerForEachHost
from vigilo.vigiconf import generator
from vigilo.vigiconf import dbexportator

from vigilo.models.session import DBSession
from vigilo.models import Host, HostApplication, Application

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
        setup_db()
        print conf
    
    def tearDown(self):
        """Call after every test case."""
        teardown_db()
        #shutil.rmtree(self.tmpdir)
    
    def test_add_host(self):
        #host = Host(conf.hostsConf, "testserver1", "192.168.1.1", "Servers")
        appendHost(u'supserver.example.com', u'testserver1')
        s = getServerToUse([u'supserver.example.com',], u'testserver1')
        self.assertEquals(s, u'supserver.example.com')
    
    def test_export_localventilation_db(self):
        ventilation = generator.get_local_ventilation()
        self.assertEquals(len(ventilation['localhost'].keys()), 14, "14 apps (%d)" % len(ventilation['localhost'].keys()))
        
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
        self.assertEquals(DBSession.query(Application).count(), 14, "14 apps in DB")
        
        dbexportator.export_ventilation_DB(ventilation)
        
        # check that for each app, localhost is supervised by itself
        for app in conf.apps.keys():
            links = DBSession.query(HostApplication).filter(HostApplication.application.has(Application.name==app)).filter(HostApplication.host==host)
            self.assertEquals(links.count(), 1, "One supervision link (%d)" % links.count())
            self.assertEquals(links.first().appserver.name, u'localhost', "superviser server is localhost")
        
    def test_ventilation_db(self):
        # check that conditions allow enterprise ventilation
        if hasattr(conf, "appsGroupsByServer"):
            try:
                from vigilo.vigiconf.lib import ventilator
            except ImportError:
                # Community Edition, ventilator is not available.
                raise
        else:
            raise Exception("conf has no attr appsGroupsByServer")
        
        ventilation = generator.getventilation()


if __name__ == '__main__':
    unittest.main()
