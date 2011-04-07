#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gestion du changement lors du chargement de

 - Dependency
"""

import unittest

from vigilo.common.conf import settings

from vigilo.vigiconf.loaders.topology import TopologyLoader
from helpers import setup_path, setup_db, teardown_db, DummyRevMan
from vigilo.models.demo import functions as df

from vigilo.models.tables import Dependency, DependencyGroup

from vigilo.models.session import DBSession


# pylint: disable-msg=W0212

class ChangeManagementTest(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        setup_db()
        self.old_conf_path = setup_path(subdir="changes")
        self.datadir = settings["vigiconf"]["confdir"]
    
        localhost = df.add_host("localhost")
        df.add_highlevelservice("hlservice1")
        df.add_lowlevelservice(localhost, "Interface eth0")
        # Pour les tests
        self.testhost1 = df.add_host("test_change_deps_1")
        self.testhost2 = df.add_host("test_change_deps_2")

    def tearDown(self):
        """Call after every test case."""
        teardown_db()
        settings["vigiconf"]["confdir"] = self.old_conf_path


    def test_change_dependencies_remove(self):
        """ Test de la gestion des changements des dépendances.
        """
        topologyloader = TopologyLoader(DummyRevMan())
        topologyloader.load_dir(self.datadir)
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
        topologyloader = TopologyLoader(DummyRevMan())
        topologyloader.has_changed = True
        topologyloader.load_dir(self.datadir)
        topologyloader.cleanup()
        depnum_after = DBSession.query(Dependency).count()
        self.assertEquals(depnum_after, depnum_before - 1)

    def test_change_dependencies_add(self):
        topologyloader = TopologyLoader(DummyRevMan())
        topologyloader.load_dir(self.datadir)
        first_dep = DBSession.query(Dependency).first()
        assert first_dep is not None
        DBSession.delete(first_dep)
        DBSession.flush()
        depnum_before = DBSession.query(Dependency).count()

        # On doit créer un 2ème loader pour forcer le rechargement
        # des instances depuis la base de données.
        topologyloader = TopologyLoader(DummyRevMan())
        topologyloader.load_dir(self.datadir)
        depnum_after = DBSession.query(Dependency).count()
        self.assertEquals(depnum_after, depnum_before + 1)

    def test_change_dependencies_nothing(self):
        topologyloader = TopologyLoader(DummyRevMan())
        topologyloader.load_dir(self.datadir)
        depnum_before = DBSession.query(Dependency).count()

        # On doit créer un 2ème loader pour forcer le rechargement
        # des instances depuis la base de données.
        topologyloader = TopologyLoader(DummyRevMan())
        topologyloader.load_dir(self.datadir)
        depnum_after = DBSession.query(Dependency).count()
        self.assertEquals(depnum_after, depnum_before)
