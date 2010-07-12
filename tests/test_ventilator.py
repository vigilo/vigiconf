#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ventilator test
"""


import os, unittest, shutil

import vigilo.vigiconf.conf as conf

from confutil import reload_conf, setup_tmpdir
from confutil import setup_db, teardown_db

from vigilo.vigiconf.lib.ventilator import appendHost, getServerToUse, \
                    findAServerForEachHost, get_host_ventilation_group
from vigilo.vigiconf import generator
from vigilo.vigiconf import dbexportator
from vigilo.vigiconf.lib import ParsingError

from vigilo.models.session import DBSession

from vigilo.models.tables import Host, Ventilation, Application, SupItemGroup
from vigilo.models.demo.functions import add_host, add_vigiloserver, add_supitemgroup

class VentilatorTest(unittest.TestCase):
    """Test Ventilator"""

    def setUp(self):
        """Call before every test case."""
        # Prepare temporary directory
        self.tmpdir = setup_tmpdir()
        os.mkdir(os.path.join(self.tmpdir, "db"))
        self.basedir = os.path.join(self.tmpdir, "deploy")
        conf.hosttemplatefactory.load_templates()
        setup_db()
        reload_conf()

    def tearDown(self):
        """Call after every test case."""
        teardown_db()
        shutil.rmtree(self.tmpdir)


    def test_export_localventilation_db(self):
        """ test de l'export de la ventilation en mode local.
        
        le remplacement de la persistance pickle par db n'est pas testée
        ici.
        """
        ventilation = generator.get_local_ventilation()
        self.assertEquals(len(ventilation['localhost'].keys()), 7, "7 apps (%d)" % len(ventilation['localhost'].keys()))
        
        # need locahost in db
        host = add_host("localhost")
        # need localhost as VigiloServer
        add_vigiloserver(u'localhost')
        
        #need apps in DB
        dbexportator.update_apps_db()
        DBSession.flush()
        self.assertEquals(DBSession.query(Application).count(), 7, "7 apps in DB")
        
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
        host = add_host("localhost")
        
        # need server
        add_vigiloserver(u'localhost')
        
        # need nagios application
        nagios = Application(name=u'nagios')
        DBSession.add(nagios)
        DBSession.flush()

        for appGroup in conf.appsGroupsByServer:
            for hostGroup in conf.appsGroupsByServer[appGroup]:
                l = conf.appsGroupsByServer[appGroup][hostGroup]
                server = getServerToUse(l, host.name)
                if one_server:
                    self.assertEquals(server, u'localhost')
        
    def test_getservertouse_multi(self):
        """ Test de la ventilation sur plusieurs serveurs vigilo.
        """
        # add 2 others servers in conf
        for appGroup in conf.appsGroupsByServer:
            for hostGroup in conf.appsGroupsByServer[appGroup]:
                conf.appsGroupsByServer[appGroup][hostGroup].append(u'supserver2.example.com')
                conf.appsGroupsByServer[appGroup][hostGroup].append(u'supserver3.example.com')
        
        # add the 2 servers in DB
        add_vigiloserver(u'supserver2.example.com')
        add_vigiloserver(u'supserver3.example.com')
        
        self.test_getservertouse(one_server=False)

    def test_host_ventilation_group(self):
        host = add_host("localhost")
        group1 = add_supitemgroup("Group1")
        group2 = add_supitemgroup("Group2", group1)
        host.groups = [group2,]
        self.assertEquals(get_host_ventilation_group("localhost", {}), "Group1")

    def test_host_ventilation_group_multiple(self):
        host = add_host("localhost")
        group1 = add_supitemgroup("Group1")
        group2 = add_supitemgroup("Group2", group1)
        group3 = add_supitemgroup("Group3", group1)
        host.groups = [group2, group3]
        self.assertEquals(get_host_ventilation_group("localhost", {}), "Group1")

    def test_host_ventilation_conflicting_groups(self):
        host = add_host("localhost")
        group1 = add_supitemgroup("Group1")
        group2 = add_supitemgroup("Group2", group1)
        group3 = add_supitemgroup("Group3")
        group4 = add_supitemgroup("Group4", group3)
        host.groups = [group2, group4]
        self.assertRaises(ParsingError, get_host_ventilation_group, "localhost", {})


if __name__ == '__main__':
    unittest.main()
