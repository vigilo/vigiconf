# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# pylint: disable-msg=C0111,W0212,R0904
"""
Tests de génération des cartes auto (refactoring)
"""

import unittest

from helpers import setup_db, teardown_db

from vigilo.models import tables
from vigilo.models.demo import functions as df
from vigilo.models.session import DBSession


class AutoMapTest(unittest.TestCase):

    def setUp(self):
        setup_db()
        self.mapgroup_root = tables.MapGroup(name=u'Root', parent=None)
        from vigilo.vigiconf.applications.vigimap import VigiMap
        self.vigimap = VigiMap()
        self.generator = self.vigimap.generator(self.vigimap, None)

    def tearDown(self):
        teardown_db()

    def test_gen_host(self):
        # Chargement en BD
        group1 = df.add_supitemgroup("Group1")
        group2 = df.add_supitemgroup("Group2", group1)
        testserver = df.add_host("testserver")
        testserver.groups.append(group2)
        # Génération
        self.generator.generate()
        # une map Linux servers
        mapgroup = tables.MapGroup.by_group_name(u"Group1")
        map_g2 = tables.Map.by_group_and_title(mapgroup, u"Group2")
        self.assertNotEquals(None, map_g2)
        self.assertEquals(1, len(map_g2.groups))
        # map Linux servers appartient au groupe Servers
        self.assertEquals(u"Group1", map_g2.groups[0].name)
        # localhost est sur la carte map_Linux servers
        self.assertEquals(1, len(map_g2.nodes))
        node = map_g2.nodes[0]
        self.assert_(isinstance(node, tables.MapNodeHost))
        self.assertEquals("testserver", node.host.name)

    def test_gen_hls(self):
        # Chargement en BD
        group1 = df.add_supitemgroup("Group1")
        group2 = df.add_supitemgroup("Group2", group1)
        testhls = df.add_highlevelservice("testhls")
        testhls.groups.append(group2)
        # Génération
        self.generator.generate()
        # une map HLS group 1
        mapgroup = tables.MapGroup.by_group_name(u"Group1")
        map_g2 = tables.Map.by_group_and_title(mapgroup, u"Group2")
        self.assertNotEquals(None, map_g2)
        # map hlsgroup1 appartient au groupe hlservices_group
        self.assertEquals(1, len(map_g2.groups))
        self.assertEquals(u"Group1", map_g2.groups[0].name)
        # le HLS est bien présent
        self.assertEquals(1, len(map_g2.nodes))
        node = map_g2.nodes[0]
        self.assert_(isinstance(node, tables.MapNodeHls))
        self.assertEquals("testhls", node.service.servicename)

    def test_gen_lls(self):
        # Chargement en BD
        group1 = df.add_supitemgroup("Group1")
        group2 = df.add_supitemgroup("Group2", group1)
        testserver = df.add_host("testserver")
        testservice = df.add_lowlevelservice(testserver, "testlls")
        testservice.groups.append(group2)
        # Génération
        self.generator.generate()
        # une map HLS group 1
        mapgroup = tables.MapGroup.by_group_name(u"Group1")
        map_g2 = tables.Map.by_group_and_title(mapgroup, u"Group2")
        self.assertNotEquals(None, map_g2)
        # map hlsgroup1 appartient au groupe hlservices_group
        self.assertEquals(1, len(map_g2.groups))
        self.assertEquals(u"Group1", map_g2.groups[0].name)
        # le HLS est bien présent
        self.assertEquals(1, len(map_g2.nodes))
        node = map_g2.nodes[0]
        self.assert_(isinstance(node, tables.MapNodeLls))
        self.assertEquals("testlls", node.service.servicename)

    def test_empty_group(self):
        # Chargement en BD
        group1 = df.add_supitemgroup("Group1")
        df.add_supitemgroup("Group2", group1)
        # Génération
        self.generator.generate()
        # pas de carte pour Group2, il ne contient rien
        self.assertEquals(None, tables.Map.by_group_and_title(group1,
                                u"Group2"))
        # et donc pas de groupe de cartes Group1, puisqu'il n'y a rien dessous
        self.assertEquals(None, tables.MapGroup.by_group_name(u"Group1"))

    def test_mapgroup(self):
        # Chargement en BD
        group1 = df.add_supitemgroup("Group1")
        group2 = df.add_supitemgroup("Group2", group1)
        group3 = df.add_supitemgroup("Group3", group2)
        testserver = df.add_host("testserver")
        testserver.groups.append(group3)
        # Génération
        self.generator.generate()
        # test de la présence des groupes
        mapgroup_base_name = self.vigimap.getConfig()["parent_topgroup"]
        print DBSession.query(tables.MapGroup).all()
        mapgroup_base = tables.MapGroup.by_group_name(
                            unicode(mapgroup_base_name))
        mapgroup1 = tables.MapGroup.by_parent_and_name(mapgroup_base,
                                                       u"Group1")
        self.assertNotEquals(None, mapgroup1)
        mapgroup2 = tables.MapGroup.by_parent_and_name(mapgroup1, u"Group2")
        self.assertNotEquals(None, mapgroup2)
        mapgroup3 = tables.Map.by_group_and_title(mapgroup2, u"Group3")
        self.assertNotEquals(None, mapgroup3)

    def test_group_rename(self):
        # Chargement en BD
        group1 = df.add_supitemgroup("Group1")
        testserver = df.add_host("testserver")
        testserver.groups.append(group1)
        # Génération
        self.generator.generate()
        mapgroup_base_name = self.vigimap.getConfig()["parent_topgroup"]
        mapgroup_base = tables.MapGroup.by_group_name(
                            unicode(mapgroup_base_name))
        map_g1 = tables.Map.by_group_and_title(mapgroup_base, u"Group1")
        self.assertNotEquals(None, map_g1)
        # Renommage
        group1.name = u"Group1 renamed"
        self.generator.generate()
        map_g1_old = tables.Map.by_group_and_title(mapgroup_base, u"Group1")
        self.assertEquals(None, map_g1_old)
        map_g1_new = tables.Map.by_group_and_title(mapgroup_base,
                                                   u"Group1 renamed")
        self.assertNotEquals(None, map_g1_new)

