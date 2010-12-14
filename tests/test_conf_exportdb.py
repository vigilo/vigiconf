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

from confutil import setup_db, teardown_db, reload_conf

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
        self.loader = LoaderManager()

    def tearDown(self):
        """Call after every test case."""
        teardown_db()

    def test_export_hosts_db(self):
        self.assertEquals(len(conf.hostsConf.items()), 1,
                          "one host in conf (%d)"%len(conf.hostsConf.items()))
        self.loader.load_conf_db()

        # check if localhost exists in db
        h = Host.by_host_name(u'localhost')
        self.assertEquals(h.name, u'localhost')

    def test_export_host_confitem(self):
        host = conf.hostsConf[u'localhost']
        host['nagiosDirectives'] = {u"max_check_attempts":u"8",
                                    u"check_interval":u"2"}

        self.loader.load_conf_db()

        ci = ConfItem.by_host_confitem_name(u'localhost', u"max_check_attempts")
        self.assertTrue(ci, "confitem max_check_attempts exists")
        self.assertEquals(ci.value, "8", "max_check_attempts=8")

        ci = ConfItem.by_host_confitem_name(u'localhost', u"check_interval")
        self.assertTrue(ci, "confitem check_interval exists")
        self.assertEquals(ci.value, "2", "check_interval=2")

    def test_export_service_confitem(self):
        host = conf.hostsConf[u'localhost']
        host['nagiosSrvDirs'][u'Interface eth0'] = {u"max_check_attempts":u"7",
                                    u"retry_interval":u"3"}

        self.loader.load_conf_db()

        ci = ConfItem.by_host_service_confitem_name(
                            u'localhost', u'Interface eth0', u"max_check_attempts")
        self.assertTrue(ci, "confitem max_check_attempts exists")
        self.assertEquals(ci.value, "7", "max_check_attempts=7")

        ci = ConfItem.by_host_service_confitem_name(
                            u'localhost', u'Interface eth0', u"retry_interval")
        self.assertTrue(ci, "confitem retry_interval exists")
        self.assertEquals(ci.value, "3", "retry_interval=3")

    def test_export_conf_db_rollback(self):
        """ Test du rollback sur la base après export en base de la conf
        """

        self.loader.load_conf_db()

        # check if localhost exists in db
        h = Host.by_host_name(u'localhost')
        self.assertEquals(h.name, u'localhost')
        self.assertEquals(h.weight, 42)

        transaction.abort()

        transaction.begin()
        # check that localhost does not exists anymore in db
        h = Host.by_host_name(u'localhost')
        self.assertFalse(h, "no more localhost host in db")

    def test_export_conf_db_commit(self):
        """ Test du commit sur la base après export en base de la conf.

        Un rollback est effectué juste après le commit.
        """

        self.loader.load_conf_db()

        # check if localhost exists in db
        h = Host.by_host_name(u'localhost')
        self.assertEquals(h.name, u'localhost')
        self.assertEquals(h.weight, 42)

        transaction.commit()

        transaction.begin()
        h = Host.by_host_name(u'localhost')
        self.assertEquals(h.name, u'localhost')
        self.assertEquals(h.weight, 42)

    def test_export_ventilation_db(self):
        from vigilo.vigiconf.lib import dispatchmodes
        from vigilo.vigiconf.lib.generators import GeneratorManager
        from vigilo.vigiconf.lib.ventilation import get_ventilator
        dispatchator = dispatchmodes.getinstance()
        genmgr = GeneratorManager(dispatchator.applications)
        ventilator = get_ventilator(dispatchator.applications)
        self.loader.load_apps_db(genmgr.apps)
        self.loader.load_conf_db()
        self.loader.load_vigilo_servers_db()

        # On doit avoir 2 serveurs de supervision : localhost & localhost2.
        # car la collecte dépend de ces deux serveurs
        # (cf. appgroups-servers.py dans le dossier de config. "general").
        nb_vigiloservers = DBSession.query(VigiloServer).count()
        self.assertEquals(nb_vigiloservers, 2)

        ventilation = ventilator.ventilate()
        self.loader.load_ventilation_db(ventilation)
        print DBSession.query(Ventilation).all()
        #
        del conf.appsGroupsByServer["trap"]

        self.loader.load_vigilo_servers_db()
        # Le nombre de serveurs de supervision ne doit pas bouger.
        nb_vigiloservers = DBSession.query(VigiloServer).count()
        self.assertEquals(nb_vigiloservers, 2)

        ventilation = ventilator.ventilate()
        self.loader.load_ventilation_db(ventilation)
        print DBSession.query(Ventilation).all()
        trap_app = DBSession.query(Application).filter_by(name=u"snmptt").first()
        trap_ventil = DBSession.query(Ventilation).filter_by(application=trap_app).count()
        self.assertEquals(trap_ventil, 0)

if __name__ == '__main__':
    unittest.main()
