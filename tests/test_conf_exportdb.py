#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
sample test
"""


import unittest

import vigilo.vigiconf.conf as conf
from vigilo.common.conf import settings
settings.load_module(__name__)

from vigilo.vigiconf.dbexportator import export_conf_db, export_ventilation_DB, update_apps_db

from confutil import setup_db, teardown_db, reload_conf

from vigilo.models.tables import Host, SupItemGroup, Ventilation, Application
from vigilo.models.session import DBSession
from vigilo.models.tables import ConfItem, Service

import transaction

class ExportDBTest(unittest.TestCase):
    """Test Sample"""

    def setUp(self):
        """Call before every test case."""
        setup_db()
        reload_conf()        
    
    def tearDown(self):
        """Call after every test case."""
        teardown_db()
    
    def test_export_hosts_db(self):
        self.assertEquals(len(conf.hostsConf.items()), 1,
                          "one host in conf (%d)"%len(conf.hostsConf.items()))
        
        export_conf_db()
        # check host groups
        nb = len(conf.hostsGroups.keys())
        
        nbdb = DBSession.query(SupItemGroup).count()
        for g in DBSession.query(SupItemGroup).all(): print g.name
        self.assertEquals(nb, nbdb, "nb hostgroups conf:%d db:%d" % (nb, nbdb))
        
        # check if localhost exists in db
        h = Host.by_host_name(u'localhost')
        self.assertEquals(h.name, u'localhost')
    
    def test_export_host_confitem(self):
        host = conf.hostsConf[u'localhost']
        host['nagiosDirectives'] = {u"max_check_attempts":u"8",
                                    u"check_interval":u"2"}
        
        export_conf_db()
        
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
        
        export_conf_db()
        
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
        
        export_conf_db()
        
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
        
        export_conf_db()
        
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
        from vigilo.vigiconf.generator import getventilation
        update_apps_db()
        export_conf_db()
        export_ventilation_DB(getventilation())
        print DBSession.query(Ventilation).all()
        #
        del conf.appsGroupsByServer["trap"]
        export_ventilation_DB(getventilation())
        print DBSession.query(Ventilation).all()
        trap_app = DBSession.query(Application).filter_by(name=u"corrtrap").first()
        trap_ventil = DBSession.query(Ventilation).filter_by(application=trap_app).count()
        self.assertEquals(trap_ventil, 0)
    

if __name__ == '__main__':
    unittest.main()
