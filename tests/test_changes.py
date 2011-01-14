#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gestion du changement lors du chargement de

 - Dependency
"""

import unittest

from vigilo.vigiconf.loaders.topology import TopologyLoader

import vigilo.vigiconf.conf as conf
from confutil import reload_conf, setup_db, teardown_db, DummyDispatchator

from vigilo.models.tables import Host
from vigilo.models.tables import LowLevelService, HighLevelService, \
                                    Dependency, DependencyGroup

from vigilo.models.session import DBSession

class ChangeManagementTest(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        setup_db()
        reload_conf()

        # Présents dans les fichiers XML
        localhost =  Host(
            name=u'localhost',
            checkhostcmd=u'halt -f',
            snmpcommunity=u'public',
            description=u'my localhost',
            hosttpl=u'template',
            address=u'127.0.0.1',
            snmpport=124,
            weight=44,
        )
        DBSession.add(localhost)
        hlservice1 = HighLevelService(
            servicename=u'hlservice1',
            # @TODO: op_dep
#            op_dep=u'+',
            message=u'Hello world',
            warning_threshold=50,
            critical_threshold=80,
            priority=1
        )
        DBSession.add(hlservice1)
        interface = LowLevelService(
            servicename=u'Interface eth0',
            weight=100,
            host=localhost
        )
        DBSession.add(interface)

        # Pour les tests
        self.testhost1 =  Host(
            name=u'test_change_deps_1',
            checkhostcmd=u'halt -f',
            snmpcommunity=u'public',
            description=u'my localhost',
            hosttpl=u'template',
            address=u'127.0.0.1',
            snmpport=42,
            weight=42,
        )
        DBSession.add(self.testhost1)
        self.testhost2 =  Host(
            name=u'test_change_deps_2',
            checkhostcmd=u'halt -f',
            snmpcommunity=u'public',
            description=u'my localhost',
            hosttpl=u'template',
            address=u'127.0.0.1',
            snmpport=42,
            weight=42,
        )
        DBSession.add(self.testhost2)
        DBSession.flush()

    def tearDown(self):
        """Call after every test case."""
        teardown_db()


    def test_change_dependencies_remove(self):
        """ Test de la gestion des changements des dépendances.
        """
        topologyloader = TopologyLoader(DummyDispatchator())
        topologyloader.load()
        dep_group = DependencyGroup(
            dependent=self.testhost1,
            operator=u'&',
            role=u'topology'
        )
        DBSession.add(dep_group)
        DBSession.flush()
        dep = Dependency(group=dep_group, supitem=self.testhost2)
        DBSession.add(dep)
        DBSession.flush()
        depnum_before = DBSession.query(Dependency).count()

        # On doit créer un 2ème loader pour forcer le rechargement
        # des instances depuis la base de données.
        topologyloader = TopologyLoader(DummyDispatchator())
        topologyloader.load()
        depnum_after = DBSession.query(Dependency).count()
        self.assertEquals(depnum_after, depnum_before - 1)

    def test_change_dependencies_add(self):
        topologyloader = TopologyLoader(DummyDispatchator())
        topologyloader.load()
        DBSession.delete(DBSession.query(Dependency).first())
        DBSession.flush()
        depnum_before = DBSession.query(Dependency).count()

        # On doit créer un 2ème loader pour forcer le rechargement
        # des instances depuis la base de données.
        topologyloader = TopologyLoader(DummyDispatchator())
        topologyloader.load()
        depnum_after = DBSession.query(Dependency).count()
        self.assertEquals(depnum_after, depnum_before + 1)

    def test_change_dependencies_nothing(self):
        topologyloader = TopologyLoader(DummyDispatchator())
        topologyloader.load()
        depnum_before = DBSession.query(Dependency).count()

        # On doit créer un 2ème loader pour forcer le rechargement
        # des instances depuis la base de données.
        topologyloader = TopologyLoader(DummyDispatchator())
        topologyloader.load()
        depnum_after = DBSession.query(Dependency).count()
        self.assertEquals(depnum_after, depnum_before)
