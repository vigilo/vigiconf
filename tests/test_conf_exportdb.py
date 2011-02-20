#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
sample test
"""


import unittest

import vigilo.vigiconf.conf as conf
from vigilo.common.conf import settings
settings.load_module(__name__)

from vigilo.vigiconf.lib.loaders import LoaderManager
from vigilo.vigiconf.loaders.group import GroupLoader
from vigilo.vigiconf.loaders.host import HostLoader
from vigilo.vigiconf.lib.confclasses.host import Host as ConfHost
from vigilo.vigiconf.applications.nagios import Nagios
from vigilo.vigiconf.applications.vigimap import VigiMap

from helpers import setup_db, teardown_db, reload_conf, DummyDispatchator

from vigilo.models.tables import Host, SupItemGroup, Ventilation, Application
from vigilo.models.session import DBSession
from vigilo.models.tables import ConfItem, Service, VigiloServer

import transaction

class ExportDBTest(unittest.TestCase):
    """Test Sample"""

    def setUp(self):
        """Call before every test case."""
        setup_db()
        reload_conf()
        self.host = ConfHost(conf.hostsConf, "dummy.xml", "testserver1",
                             "192.168.1.1", "Servers")
        self.loader = LoaderManager(DummyDispatchator())

    def tearDown(self):
        """Call after every test case."""
        teardown_db()

    def test_export_hosts_db(self):
        self.assertEquals(len(conf.hostsConf.items()), 1,
                          "there should be one host in conf")
        #self.loader.load_conf_db()
        d = DummyDispatchator()
        grouploader = GroupLoader(d)
        hostloader = HostLoader(grouploader, d)
        hostloader.load()
        # check if testserver1 exists in db
        h = Host.by_host_name(u'testserver1')
        self.assertNotEqual(h, None)
        self.assertEqual(h.name, u'testserver1')
        self.assertEqual(h.address, u'192.168.1.1')

    def test_export_host_confitem(self):
        host = conf.hostsConf[u'testserver1']
        host['nagiosDirectives'] = {u"max_check_attempts": u"8",
                                    u"check_interval": u"2"}

        #self.loader.load_conf_db()
        d = DummyDispatchator()
        grouploader = GroupLoader(d)
        hostloader = HostLoader(grouploader, d)
        hostloader.load()

        ci = ConfItem.by_host_confitem_name(u"testserver1",
                                            u"max_check_attempts")
        self.assertNotEqual(ci, None, "confitem max_check_attempts must exist")
        self.assertEqual(ci.value, "8", "max_check_attempts=8")

        ci = ConfItem.by_host_confitem_name(u"testserver1", u"check_interval")
        self.assertNotEqual(ci, None, "confitem check_interval must exist")
        self.assertEquals(ci.value, "2", "check_interval=2")

    def test_export_service_confitem(self):
        self.host.add_external_sup_service("Interface eth0")
        host = conf.hostsConf[u'testserver1']
        host['nagiosSrvDirs'][u'Interface eth0'] = {
                                    u"max_check_attempts": u"7",
                                    u"retry_interval": u"3"}

        #self.loader.load_conf_db()
        d = DummyDispatchator()
        grouploader = GroupLoader(d)
        hostloader = HostLoader(grouploader, d)
        hostloader.load()

        ci = ConfItem.by_host_service_confitem_name(
                            u'testserver1', u'Interface eth0',
                            u"max_check_attempts")
        self.assertTrue(ci, "confitem max_check_attempts must exist")
        self.assertEquals(ci.value, "7", "max_check_attempts=7")

        ci = ConfItem.by_host_service_confitem_name(
                            u'testserver1', u'Interface eth0',
                            u"retry_interval")
        self.assertTrue(ci, "confitem retry_interval must exist")
        self.assertEquals(ci.value, "3", "retry_interval=3")

    def test_export_ventilation_db(self):
        """
        Export de la ventilation en BdD.
        On ventile une première fois, puis on supprime une application et on
        re-ventile. L'application ne doit plus être ventilée en BdD
        """
        from vigilo.vigiconf.lib import dispatchmodes
        from vigilo.vigiconf.lib.generators import GeneratorManager
        from vigilo.vigiconf.lib.ventilation import get_ventilator
        conf.appsGroupsByServer = {
                    "interface": {
                        "Servers": [u"sup.example.com"],
                    },
                    "collect": {
                        "Servers": [u"sup.example.com"],
                    },
                    "trap": {
                        "Servers": [u"sup.example.com"],
                    },
                }
        dispatchator = DummyDispatchator()
        grouploader = GroupLoader(dispatchator)
        hostloader = HostLoader(grouploader, dispatchator)
        nagios = Nagios()
        vigimap = VigiMap()
        genmgr = GeneratorManager([nagios, vigimap], DummyDispatchator())
        ventilator = get_ventilator([nagios, vigimap])
        self.loader.load_apps_db(genmgr.apps)
        hostloader.load()
        self.loader.load_vigilo_servers_db()

        nb_vigiloservers = DBSession.query(VigiloServer).count()
        self.assertEquals(nb_vigiloservers, 1)

        ventilation = ventilator.ventilate()
        self.loader.load_ventilation_db(ventilation, [nagios, vigimap])
        print DBSession.query(Ventilation).all()
        #
        del conf.appsGroupsByServer["trap"]

        self.loader.load_vigilo_servers_db()
        # Le nombre de serveurs de supervision ne doit pas bouger.
        nb_vigiloservers = DBSession.query(VigiloServer).count()
        self.assertEquals(nb_vigiloservers, 1)

        ventilation = ventilator.ventilate()
        self.loader.load_ventilation_db(ventilation, [nagios, vigimap])
        print DBSession.query(Ventilation).all()
        trap_app = DBSession.query(Application).filter_by(name=u"snmptt").first()
        trap_ventil = DBSession.query(Ventilation).filter_by(application=trap_app).count()
        self.assertEquals(trap_ventil, 0)

if __name__ == '__main__':
    unittest.main()
