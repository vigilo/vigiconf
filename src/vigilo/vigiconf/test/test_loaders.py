# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# pylint: disable-msg=C0111,W0212,R0904
# Copyright (C) 2006-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>
from __future__ import absolute_import

import os
import unittest

from vigilo.models.tables import SupItemGroup, SupItemGroup
from vigilo.models.tables.grouphierarchy import GroupHierarchy
from vigilo.models.session import DBSession

from vigilo.vigiconf.loaders.group import GroupLoader

from .helpers import setup_db, teardown_db, TESTDATADIR


class XMLLoaderTest(unittest.TestCase):

    def setUp(self):
        setup_db()
        DBSession.query(SupItemGroup).delete()
        DBSession.query(GroupHierarchy).delete()
        DBSession.flush()

    def tearDown(self):
        teardown_db()


class GroupLoaderTest(XMLLoaderTest):

    def setUp(self):
        super(GroupLoaderTest, self).setUp()
        self.grouploader = GroupLoader()

    def test_load_hostgroups(self):
        self.grouploader.load_dir(os.path.join(TESTDATADIR, "xsd",
                                  "hostgroups", "ok"))

        g = SupItemGroup.by_group_name(u'root_group')
        self.assertTrue(g, "root_group is not created.")
        n = len(g.get_children())
        #c = SupItemGroup.by_group_name(u'hgroup1')
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

        num = DBSession.query(SupItemGroup).filter_by(
                    name=u"Linux servers 4").count()
        self.assertEquals(num, 2, "Linux servers 4 is not doubled in DB")

    def test_hostgroups_hierarchy(self):
        """
        Test de grouploader.get_groups_hierarchy()
        Réimplémentation avec db du dico python conf.groupsHierarchy
        """
        self.grouploader.load_dir(os.path.join(TESTDATADIR,
                                  'xsd/hostgroups/ok'))
        gh = self.grouploader._in_conf
        print gh
        self.assertTrue("/root_group3/hgroup31" in gh)
        self.assertTrue("/root_group3/hgroup33/Linux servers 3" in gh)
