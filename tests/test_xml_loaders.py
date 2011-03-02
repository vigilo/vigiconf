#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
loaders test.

 * host groups
 * service groups
 * topology
"""

import os, unittest, shutil

from vigilo.vigiconf.lib import ParsingError
from vigilo.vigiconf.loaders.group import GroupLoader
from vigilo.vigiconf.loaders.topology import TopologyLoader

import vigilo.vigiconf.conf as conf
from helpers import setup_db, teardown_db, DummyRevMan

from vigilo.models.tables import SupItemGroup, SupItemGroup, Host, SupItem
from vigilo.models.tables import LowLevelService, HighLevelService, \
                                    Dependency, DependencyGroup
from vigilo.models.tables.grouphierarchy import GroupHierarchy
from vigilo.models.session import DBSession
from vigilo.models.demo import functions as df


class XMLLoaderTest(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        setup_db()
        #reload_conf()
        DBSession.query(SupItemGroup).delete()
        DBSession.query(GroupHierarchy).delete()
        DBSession.flush()

    def tearDown(self):
        """Call after every test case."""
        teardown_db()


class GroupLoaderTest(XMLLoaderTest):

    def setUp(self):
        super(GroupLoaderTest, self).setUp()
        self.grouploader = GroupLoader()

    def test_load_hostgroups(self):
        self.grouploader.load_dir('tests/testdata/xsd/hostgroups/ok')

        g = SupItemGroup.by_group_name(u'root_group')
        self.assertTrue(g, "root_group created.")
        n = len(g.get_children())
        c = SupItemGroup.by_group_name(u'hgroup1')
        print g.get_children()
        self.assertEquals(n, 3, "rootgroup has 3 children (%d)" % n)

        g = SupItemGroup.by_group_name(u'root_group3')
        self.assertTrue(g, "root_group3 created.")
        n = len(g.get_children())
        self.assertEquals(n, 3, "rootgroup3 has 3 children (%d)" % n)

        g = SupItemGroup.by_group_name(u'root_group2')
        self.assertTrue(g, "root_group2 created.")
        n = len(g.get_children())
        self.assertEquals(n, 3, "rootgroup2 has 3 children (%d)" % n)

        num = DBSession.query(SupItemGroup).filter_by(name=u"Linux servers 4").count()
        self.assertEquals(num, 2, "Linux servers 4 is not doubled in DB")

    #def test_load_hostgroups_ko(self):
    #    basedir = 'tests/testdata/xsd/hostgroups/ko/loader_ko'
    #    self.assertRaises(Exception, self.grouploader.load_dir, '%s/1' % basedir)


class DepLoaderTest(XMLLoaderTest):

    def setUp(self):
        super(DepLoaderTest, self).setUp()
        self.grouploader = GroupLoader()
        self.topologyloader = TopologyLoader(DummyRevMan())
        self.host1 = df.add_host("host1")
        self.host11 = df.add_host("host11")
        self.host12 = df.add_host("host12")
        self.service11 = df.add_lowlevelservice(self.host11, "service11")
        self.service12 = df.add_lowlevelservice(self.host12, "service12")

    def test_load_topologies(self):
        # let's create hosts and services
        print DBSession.query(Dependency).count()
        self.topologyloader.load_dir('tests/testdata/xsd/topologies/ok/loader')
        # 4 topologies
        self.assertEquals(2, DBSession.query(Dependency).count())
        # host11/service11 is a dependence of host1
        si_host1 = SupItem.get_supitem(hostname=u"host1", servicename=None)
        si_host11 = SupItem.get_supitem(hostname=u"host11", servicename=u"service11")
        self.assertTrue(si_host1, "si_host1 not null")
        self.assertTrue(si_host11, "si_host11 not null")
        self.assertEquals(1,
            DBSession.query(
                    Dependency
                ).join(
                    (DependencyGroup, DependencyGroup.idgroup == \
                        Dependency.idgroup),
                ).filter(DependencyGroup.iddependent == si_host1
                ).filter(Dependency.idsupitem == si_host11
                ).count(),
          "One dependency: host1 depends on host11/service11")

    def test_load_conf_topologies(self):
        """Test de chargement des dépendances de la conf"""
        localhost = df.add_host("localhost")
        interface = df.add_lowlevelservice(localhost, "Interface eth0")
        self.topologyloader.load_dir('tests/testdata/conf.d/topologies')

    def test_load_topologies_ko(self):
        """
        Test de fichiers xml valides selon XSD mais invalides pour le loader.
        """
        basedir = 'tests/testdata/xsd/topologies/ok/loader_ko'
        self.assertRaises(ParsingError, self.topologyloader.load_dir, basedir)

    def test_hostgroups_hierarchy(self):
        """
        Test de grouploader.get_groups_hierarchy()
        Réimplémentation avec db du dico python conf.groupsHierarchy
        """
        self.grouploader.load_dir('tests/testdata/xsd/hostgroups/ok')
        gh = self.grouploader._in_conf
        print gh
        self.assertTrue("/root_group3/hgroup31" in gh)
        self.assertTrue("/root_group3/hgroup33/Linux servers 3" in gh)
