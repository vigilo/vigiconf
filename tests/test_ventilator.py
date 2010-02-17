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

#from vigilo.models.session import DBSession
from vigilo.models.configure import DBSession

from vigilo.models import Host, Ventilation, Application, VigiloServer

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
    
    def tearDown(self):
        """Call after every test case."""
        teardown_db()
        shutil.rmtree(self.tmpdir)
        
    def _create_localhost(self):
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
        return host
        
    def _create_vigiloserver(self, name):
        v = VigiloServer(name=name)
        DBSession.add(v)
        DBSession.flush()
        return v
    
    def test_export_localventilation_db(self):
        """ test de l'export de la ventilation en mode local.
        
        le remplacement de la persistance pickle par db n'est pas testée
        ici.
        """
        ventilation = generator.get_local_ventilation()
        self.assertEquals(len(ventilation['localhost'].keys()), 10, "10 apps (%d)" % len(ventilation['localhost'].keys()))
        
        # need locahost in db
        host = self._create_localhost()
        # need localhost as VigiloServer
        self._create_vigiloserver(u'localhost')
        
        #need apps in DB
        dbexportator.update_apps_db()
        self.assertEquals(DBSession.query(Application).count(), 10, "10 apps in DB")
        
        dbexportator.export_ventilation_DB(ventilation)
        
        # check that for each app, localhost is supervised by itself
        for app in conf.apps.keys():
            links = DBSession.query(Ventilation).filter(Ventilation.application.has(Application.name==app)).filter(Ventilation.host==host)
            self.assertEquals(links.count(), 1, "One supervision link (%d)" % links.count())
            self.assertEquals(links.first().vigiloserver.name, u'localhost', "superviser server is localhost")
        
    def test_getservertouse(self, one_server=True):
        """ Test de la nouvelle persistance db remplaçant la persistance pickle.
        """
        # need locahost in db
        host = self._create_localhost()
        
        # need server
        self._create_vigiloserver(u'supserver.example.com')
        
        # need nagios application
        # TODO: no more
        nagios = Application(name=u'nagios')
        DBSession.add(nagios)
        DBSession.flush()

        for appGroup in conf.appsGroupsByServer:
            for hostGroup in conf.appsGroupsByServer[appGroup]:
                l = conf.appsGroupsByServer[appGroup][hostGroup]
                server = getServerToUse(l, host.name)
                if one_server:
                    self.assertEquals(server, u'supserver.example.com')
        
    def test_getservertouse_multi(self):
        """ Test de la ventilation sur plusieurs serveurs vigilo.
        """
        # add 2 others servers in conf
        for appGroup in conf.appsGroupsByServer:
            for hostGroup in conf.appsGroupsByServer[appGroup]:
                conf.appsGroupsByServer[appGroup][hostGroup].append(u'supserver2.example.com')
                conf.appsGroupsByServer[appGroup][hostGroup].append(u'supserver3.example.com')
        
        # add the 2 servers in DB
        self._create_vigiloserver(u'supserver2.example.com')
        self._create_vigiloserver(u'supserver3.example.com')
        
        self.test_getservertouse(one_server=False)


if __name__ == '__main__':
    unittest.main()
