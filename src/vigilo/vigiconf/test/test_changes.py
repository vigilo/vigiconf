#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gestion du changement lors du chargement de

 - Dependency
"""

import unittest

from vigilo.common.conf import settings
from vigilo.models.demo import functions as df
from vigilo.models.tables import SupItemGroup
from vigilo.models.session import DBSession

from vigilo.vigiconf.loaders.group import GroupLoader
from helpers import setup_path, setup_db, teardown_db


# pylint: disable-msg=W0212,C0111

class ChangeManagementTest(unittest.TestCase):

    def setUp(self):
        setup_db()
        self.old_conf_path = setup_path(subdir="changes")
        self.datadir = settings["vigiconf"]["confdir"]
    
        #localhost = df.add_host("localhost")
        #df.add_highlevelservice("hlservice1")
        #df.add_lowlevelservice(localhost, "Interface eth0")
        # Pour les tests
        #self.testhost1 = df.add_host("test_change_deps_1")
        #self.testhost2 = df.add_host("test_change_deps_2")

    def tearDown(self):
        teardown_db()
        settings["vigiconf"]["confdir"] = self.old_conf_path


    def test_change_dependencies_remove(self):
        """Gestion des changements: fichier supprimé"""
        grouploader = GroupLoader()
        grouploader.load_dir(self.datadir)
        df.add_supitemgroup("to_be_removed")
        before = DBSession.query(SupItemGroup).count()
        # On doit créer un 2ème loader pour forcer le rechargement
        # des instances depuis la base de données.
        grouploader = GroupLoader()
        grouploader.load_dir(self.datadir)
        grouploader.cleanup()
        after = DBSession.query(SupItemGroup).count()
        self.assertEquals(after, before - 1)

    def test_change_dependencies_add(self):
        grouploader = GroupLoader()
        grouploader.load_dir(self.datadir)
        print DBSession.query(SupItemGroup).all()
        first_group = DBSession.query(SupItemGroup).first()
        assert first_group is not None
        DBSession.delete(first_group)
        DBSession.flush()
        before = DBSession.query(SupItemGroup).count()
        # On doit créer un 2ème loader pour forcer le rechargement
        # des instances depuis la base de données.
        grouploader = GroupLoader()
        grouploader.load_dir(self.datadir)
        after = DBSession.query(SupItemGroup).count()
        self.assertEquals(after, before + 1)

    def test_change_dependencies_nothing(self):
        grouploader = GroupLoader()
        grouploader.load_dir(self.datadir)
        before = DBSession.query(SupItemGroup).count()
        # On doit créer un 2ème loader pour forcer le rechargement
        # des instances depuis la base de données.
        grouploader = GroupLoader()
        grouploader.load_dir(self.datadir)
        after = DBSession.query(SupItemGroup).count()
        self.assertEquals(after, before)
