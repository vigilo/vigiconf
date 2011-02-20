#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gestion du changement lors du chargement de

 - Dependency
"""

import unittest

from vigilo.vigiconf.loaders.topology import TopologyLoader

import vigilo.vigiconf.conf as conf
from helpers import reload_conf, setup_db, teardown_db, DummyDispatchator
from vigilo.models.demo import functions as df

from vigilo.models import tables
from vigilo.models.tables import Dependency, DependencyGroup

from vigilo.models.session import DBSession


class ChangeManagementTest(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        setup_db()
        reload_conf()
    
        localhost = df.add_host("localhost")
        hlservice1 = df.add_highlevelservice("hlservice1")
        interface = df.add_lowlevelservice(localhost, "Interface eth0")
        # Pour les tests
        self.testhost1 = df.add_host("test_change_deps_1")
        self.testhost2 = df.add_host("test_change_deps_2")

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
