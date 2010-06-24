#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
loaders test.

 * host groups
 * service groups
 * dependencies
"""

import os, unittest, shutil

from vigilo.vigiconf.lib import ParsingError
from vigilo.vigiconf.loaders.group import GroupLoader
from vigilo.vigiconf.loaders.dependency import DependencyLoader

import vigilo.vigiconf.conf as conf
from confutil import reload_conf, setup_db, teardown_db

from vigilo.models.tables import SupItemGroup, SupItemGroup, Host, SupItem
from vigilo.models.tables import LowLevelService, HighLevelService, Dependency
from vigilo.models.session import DBSession


class XMLLoaderTest(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        reload_conf()
        setup_db()
        
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
        self.dependencyloader = DependencyLoader()
        self.host1 =  Host(
            name=u'host1',
            checkhostcmd=u'halt -f',
            snmpcommunity=u'public',
            description=u'My Host 1',
            hosttpl=u'template',
            mainip=u'127.0.0.1',
            snmpport=1234,
            weight=42,
        )
        DBSession.add(self.host1)
        self.host11 =  Host(
            name=u'host11',
            checkhostcmd=u'halt -f',
            snmpcommunity=u'public',
            description=u'My Host 11',
            hosttpl=u'tSemplate',
            mainip=u'127.0.0.2',
            snmpport=123,
            weight=43,
        )
        DBSession.add(self.host11)
        self.host12 =  Host(
            name=u'host12',
            checkhostcmd=u'halt -f',
            snmpcommunity=u'public',
            description=u'My Host 12',
            hosttpl=u'template',
            mainip=u'127.0.0.3',
            snmpport=124,
            weight=44,
        )
        DBSession.add(self.host12)
        self.hlservice1 = HighLevelService(
            servicename=u'hlservice1',
            op_dep=u'+',
            message=u'Hello world',
            warning_threshold=50,
            critical_threshold=80,
            priority=1
        )
        DBSession.add(self.hlservice1)
        self.service11 = LowLevelService(
            servicename=u'service11',
            op_dep=u'+',
            weight=100,
            host=self.host11
        )
        DBSession.add(self.service11)
        self.service12 = LowLevelService(
            servicename=u'service12',
            op_dep=u'+',
            weight=100,
            host=self.host12
        )
        DBSession.add(self.service12)
        DBSession.flush()

    def test_load_dependencies(self):
        # let's create hosts and services
        
        
        print DBSession.query(Dependency).count()
        self.dependencyloader.load_dir('tests/testdata/xsd/dependencies/ok/loader')
        
        """ The dependency links are as following:
        <dependency>
            <host name="host1" />
            <!-- always high level services here -->
            <service name="hlservice1" />
            
            <subitems>
                <host name="host11" />
                <host name="host12" />
                
                <!-- low level services supported by each host above -->
                <!-- or high level services if no host in the subitems section -->
                <service name="service11" />
                <service name="service12" />
            </subitems>
            
        </dependency>
        """
        # 4 dependencies
        self.assertEquals(4, DBSession.query(Dependency).count(), "4 dependencies")
        # host11/service11 is a dependence of host1
        
        si_host1 = SupItem.get_supitem(hostname=u"host1", servicename=None)
        si_host11 = SupItem.get_supitem(hostname=u"host11", servicename=u"service11")
        self.assertTrue(si_host1, "si_host1 not null")
        self.assertTrue(si_host11, "si_host11 not null")
        self.assertEquals(1,
          DBSession.query(Dependency).filter(Dependency.idsupitem1==si_host1)\
                                     .filter(Dependency.idsupitem2==si_host11)\
                                     .count(),
          "One dependency: host11/service11 is a dependence of host1")
        
        # host11/service11 is a dependence of hlservice1
        si_hls1 = SupItem.get_supitem(hostname=None, servicename=u"hlservice1")
        self.assertEquals(1,
          DBSession.query(Dependency).filter(Dependency.idsupitem1==si_hls1)\
                                     .filter(Dependency.idsupitem2==si_host11)\
                                     .count(),
          "One dependency: host11/service11 is a dependence of hlservice1")
    
    def test_load_conf_dependencies(self):
        """ Test de chargement des dépendances de la conf.
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
        
        interface = LowLevelService(
            servicename=u'Interface eth0',
            op_dep=u'+',
            weight=100,
            host=localhost
        )
        DBSession.add(interface)
        DBSession.flush()
        
        self.dependencyloader.load_dir('tests/testdata/conf.d/dependencies')
    
    def test_load_dependencies_ko(self):
        """ Test de fichiers xml valides selon XSD mais invalides pour le loader.
        
        """
        basedir = 'tests/testdata/xsd/dependencies/ok/loader_ko'
        
        self.assertRaises(ParsingError, self.dependencyloader.load_dir, basedir)
        
    def test_hostgroups_hierarchy(self):
        """ Test de grouploader.get_groups_hierarchy().
        
        réimplémentation avec db du dico python conf.groupsHierarchy
        """
        self.grouploader.load_dir('tests/testdata/xsd/hostgroups/ok')
        gh = self.grouploader.get_groups_hierarchy()
        #print gh
        self.assertEquals(len(gh.keys()), 3, "3 top hostgroups")
        self.assertEquals(gh["root_group3"]["hgroup31"], 1)
        self.assertEquals(gh["root_group3"]["hgroup33"]["Linux servers 3"], 1)
            
