# -*- coding: utf-8 -*-

import unittest

from vigilo.common.conf import settings

from helpers import setup_db, teardown_db, setup_path
from vigilo.vigiconf.loaders.group import GroupLoader
from vigilo.models.session import DBSession
from vigilo.models.tables import SupItemGroup

# pylint: disable-msg=W0212,C0111

class TestSplitGroup(unittest.TestCase):
    def setUp(self):
        super(TestSplitGroup, self).setUp()
        self.old_conf_path = setup_path(subdir="split_group")
        setup_db()

    def tearDown(self):
        teardown_db()
        super(TestSplitGroup, self).tearDown()
        settings["vigiconf"]["confdir"] = self.old_conf_path

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
