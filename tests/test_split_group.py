# -*- coding: utf-8 -*-

import unittest

from helpers import setup_db, teardown_db, setup_path
from vigilo.vigiconf.loaders.group import GroupLoader
from vigilo.models.session import DBSession
from vigilo.models.tables import SupItemGroup

class TestSplitGroup(unittest.TestCase):
    def setUp(self):
        super(TestSplitGroup, self).setUp()
        setup_path(subdir="split_group")
        setup_db()

    def tearDown(self):
        teardown_db()
        super(TestSplitGroup, self).tearDown()

    def test_split_group(self):
        """Test l'éclatement de la définition des groupes (#336)"""
        # Chargement des groupes.
        grouploader = GroupLoader()
        grouploader.load()
        DBSession.flush()

        # Vérification des groupes créés.
        split_group = DBSession.query(
                SupItemGroup
            ).filter(SupItemGroup.name == u'split_group'
            ).one()

        children = split_group.children
        self.assertEquals(2, len(children), "2 groupes fils attendus")
        names = [c.name for c in children]
        names.sort()
        self.assertEquals([u'bar', u'foo'], names)
