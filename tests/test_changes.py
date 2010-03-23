#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gestion du changement lors du chargement de

 - Dependency
"""

import unittest

from vigilo.vigiconf.loaders import dependencyloader

import vigilo.vigiconf.conf as conf
from confutil import reload_conf, setup_db, teardown_db

from vigilo.models import Host
from vigilo.models import LowLevelService, HighLevelService, Dependency

from vigilo.models.configure import DBSession

class ChangeManagementTest(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        reload_conf()
        setup_db()
        
    def tearDown(self):
        """Call after every test case."""
        teardown_db()

    
    def test_change_dependencies(self):
        """ Test de la gestion des changements des dépendances.
        """
        localhost =  Host(
            name=u'localhost',
            checkhostcmd=u'halt -f',
            snmpcommunity=u'public',
            description=u'my localhost',
            hosttpl=u'template',
            mainip=u'127.0.0.1',
            snmpport=124,
            weight=44,
        )
        DBSession.add(localhost)
        
        hlservice1 = HighLevelService(
            servicename=u'hlservice1',
            op_dep=u'+',
            message=u'Hello world',
            warning_threshold=50,
            critical_threshold=80,
            priority=1
        )
        DBSession.add(hlservice1)
        
        interface = LowLevelService(
            servicename=u'Interface eth0',
            op_dep=u'+',
            weight=100,
            host=localhost
        )
        DBSession.add(interface)
        
        dependencyloader.reset_change()
        dependencyloader.load_dir('src/vigilo/vigiconf/conf.d/dependencies', delete_all=False)
        self.assertTrue(
                        dependencyloader.detect_change(),
                        "changes: entities creation")
        
        dependencyloader.reset_change()
        dependencyloader.load_dir('src/vigilo/vigiconf/conf.d/dependencies', delete_all=True)
        self.assertFalse(
                        dependencyloader.detect_change(),
                        "no change")
        
        # suppression d'une dép
        DBSession.delete( DBSession.query(Dependency).all()[-1] )
        
        dependencyloader.reset_change()
        dependencyloader.load_dir('src/vigilo/vigiconf/conf.d/dependencies', delete_all=True)
        
        self.assertTrue(
                        dependencyloader.detect_change(),
                        "one dependency re-created")
