# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# pylint: disable-msg=W0212,C0111,R0904
# Copyright (C) 2006-2013 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Gestion du changement lors du chargement des fichiers XML
"""
from __future__ import absolute_import

import unittest

from vigilo.common.conf import settings
from vigilo.models.demo import functions as df
from vigilo.models.tables import SupItemGroup
from vigilo.models.session import DBSession

from vigilo.vigiconf.loaders.group import GroupLoader
from .helpers import setup_path, setup_db, teardown_db


class ChangeManagementTest(unittest.TestCase):

    def setUp(self):
        setup_db()
        self.old_conf_path = setup_path(subdir="changes")
        self.datadir = settings["vigiconf"]["confdir"]

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
