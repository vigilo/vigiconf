#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
loaders test.

 * host groups
 * service groups
 * dependencies
"""

import os, unittest, shutil

from vigilo.vigiconf.loaders import grouploader, \
                                    dependencyloader

import vigilo.vigiconf.conf as conf
from confutil import reload_conf, setup_db, teardown_db

from vigilo.models.tables import SupItemGroup, SupItemGroup, Host, SupItem
from vigilo.models.tables import LowLevelService, HighLevelService, Dependency
from vigilo.models.session import DBSession

class XMLLoadersTest(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        reload_conf()
        setup_db()
        
    def tearDown(self):
        """Call after every test case."""
        teardown_db()

        
    def test_load_hostgroups(self):
        grouploader.load_dir('tests/testdata/xsd/hostgroups/ok')
        
        g = SupItemGroup.by_group_name('root_group')
        self.assertTrue(g, "root_group created.")
        n = len(g.get_children())
        self.assertEquals(n, 3, "rootgroup has 3 children (%d)" % n)
        
        g = SupItemGroup.by_group_name('root_group3')
        self.assertTrue(g, "root_group3 created.")
        n = len(g.get_children())
        self.assertEquals(n, 3, "rootgroup3 has 3 children (%d)" % n)
        
        g = SupItemGroup.by_group_name('root_group2')
        self.assertTrue(g, "root_group2 created.")
        n = len(g.get_children())
        self.assertEquals(n, 3, "rootgroup2 has 3 children (%d)" % n)
        
    def test_load_hostgroups_ko(self):
        basedir = 'tests/testdata/xsd/hostgroups/ko/loader_ko'
        
        self.assertRaises(Exception, grouploader.load_dir, '%s/1' % basedir)
        
    def test_load_dependencies(self):
        # let's create hosts and services
        host1 =  Host(
            name=u'host1',
            checkhostcmd=u'halt -f',
            snmpcommunity=u'public',
            description=u'My Host 1',
            hosttpl=u'template',
            mainip=u'127.0.0.1',
            snmpport=1234,
            weight=42,
        )
        DBSession.add(host1)
        host11 =  Host(
            name=u'host11',
            checkhostcmd=u'halt -f',
            snmpcommunity=u'public',
            description=u'My Host 11',
            hosttpl=u'tSemplate',
            mainip=u'127.0.0.2',
            snmpport=123,
            weight=43,
        )
        DBSession.add(host11)
        host12 =  Host(
            name=u'host12',
            checkhostcmd=u'halt -f',
            snmpcommunity=u'public',
            description=u'My Host 12',
            hosttpl=u'template',
            mainip=u'127.0.0.3',
            snmpport=124,
            weight=44,
        )
        DBSession.add(host12)
        
        hlservice1 = HighLevelService(
            servicename=u'hlservice1',
            op_dep=u'+',
            message=u'Hello world',
            warning_threshold=50,
            critical_threshold=80,
            priority=1
        )
        DBSession.add(hlservice1)
        
        service11 = LowLevelService(
            servicename=u'service11',
            op_dep=u'+',
            weight=100,
            host=host11
        )
        DBSession.add(service11)
        
        service12 = LowLevelService(
            servicename=u'service12',
            op_dep=u'+',
            weight=100,
            host=host12
        )
        DBSession.add(service12)
        DBSession.flush()
        
        dependencyloader.load_dir('tests/testdata/xsd/dependencies/ok/loader')
        
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
        # 8 dependencies
        self.assertEquals(8, DBSession.query(Dependency).count(), "8 dependencies")
        # host11/service11 is a dependence of host1
        
        si_host1 = SupItem.get_supitem(hostname="host1", servicename=None)
        si_host11 = SupItem.get_supitem(hostname="host11", servicename="service11")
        self.assertTrue(si_host1, "si_host1 not null")
        self.assertTrue(si_host11, "si_host11 not null")
        self.assertEquals(1,
          DBSession.query(Dependency).filter(Dependency.idsupitem1==si_host1)\
                                     .filter(Dependency.idsupitem2==si_host11)\
                                     .count(),
          "One dependency: host11/service11 is a dependence of host1")
        
        # host11/service11 is a dependence of hlservice1
        si_hls1 = SupItem.get_supitem(hostname=None, servicename="hlservice1")
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
        
        dependencyloader.load_dir('src/vigilo/vigiconf/conf.d/dependencies')
    
    def test_load_dependencies_ko(self):
        """ Test de fichiers xml valides selon XSD mais invalides pour le loader.
        
        """
        host1 =  Host(
            name=u'host1',
            checkhostcmd=u'halt -f',
            snmpcommunity=u'public',
            description=u'My Host 1',
            hosttpl=u'template',
            mainip=u'127.0.0.1',
            snmpport=1234,
            weight=42,
        )
        DBSession.add(host1)
        host11 =  Host(
            name=u'host11',
            checkhostcmd=u'halt -f',
            snmpcommunity=u'public',
            description=u'My Host 11',
            hosttpl=u'tSemplate',
            mainip=u'127.0.0.2',
            snmpport=123,
            weight=43,
        )
        DBSession.add(host11)
        host12 =  Host(
            name=u'host12',
            checkhostcmd=u'halt -f',
            snmpcommunity=u'public',
            description=u'My Host 12',
            hosttpl=u'template',
            mainip=u'127.0.0.3',
            snmpport=124,
            weight=44,
        )
        DBSession.add(host12)
        
        hlservice1 = HighLevelService(
            servicename=u'hlservice1',
            op_dep=u'+',
            message=u'Hello world',
            warning_threshold=50,
            critical_threshold=80,
            priority=1
        )
        DBSession.add(hlservice1)
        
        service11 = LowLevelService(
            servicename=u'service11',
            op_dep=u'+',
            weight=100,
            host=host11
        )
        DBSession.add(service11)
        
        service12 = LowLevelService(
            servicename=u'service12',
            op_dep=u'+',
            weight=100,
            host=host12
        )
        DBSession.add(service12)
        DBSession.flush()
        
        basedir = 'tests/testdata/xsd/dependencies/ok/loader_ko'
        
        self.assertRaises(Exception, dependencyloader.load_dir, "%s/1" % basedir)
        
        self.assertRaises(Exception, dependencyloader.load_dir, "%s/2" % basedir)
        
        self.assertRaises(Exception, dependencyloader.load_dir, "%s/3" % basedir)
        
        self.assertRaises(Exception, dependencyloader.load_dir, "%s/4" % basedir)
        
    def test_hostgroups_hierarchy(self):
        """ Test de grouploader.get_groups_hierarchy().
        
        réimplémentation avec db du dico python conf.groupsHierarchy
        """
        grouploader.load_dir('tests/testdata/xsd/hostgroups/ok')
        gh = grouploader.get_groups_hierarchy()
        print gh
        self.assertEquals(len(gh.keys()), 3, "3 top hostgroups")
        self.assertEquals(gh["root_group3"]["hgroup31"], 1)
        self.assertEquals(gh["root_group3"]["hgroup33"]["Linux servers 3"], 1)
            
