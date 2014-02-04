# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# pylint: disable-msg=C0111,W0212,R0904
# Copyright (C) 2006-2014 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Tests sur le gestionnaire de dépôt SVN (RevisionManager)
"""
from __future__ import absolute_import

import os
import shutil
import subprocess
import unittest

from vigilo.common.conf import settings

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.models.session import DBSession
from vigilo.models import tables

from vigilo.vigiconf.lib.dispatchator.revisionmanager import RevisionManager

from .helpers import setup_tmpdir, LoggingCommandFactory
from .helpers import setup_db, teardown_db


class RevisionManagerTest(unittest.TestCase):

    def setUp(self):
        setup_db()
        # Répertoires
        self.tmpdir = setup_tmpdir()
        self.confdir = os.path.join(self.tmpdir, "conf.d")
        settings["vigiconf"]["confdir"] = self.confdir
        # Créer le dépôt SVN
        repopath = os.path.join(self.tmpdir, "svn")
        settings["vigiconf"]["svnrepository"] = "file://%s" % repopath
        try:
            subprocess.call(["svnadmin", "create", repopath])
        except OSError:
            self.fail("La commande \"svnadmin\" n'est pas disponible")
        self._run_svn(["checkout", "file://%s" % repopath, self.confdir])
        for subdir in ["general", "hosts"]:
            os.mkdir(os.path.join(self.confdir, subdir))
            self._run_svn(["add", os.path.join(self.confdir, subdir)])
        self._run_svn(["commit", "-m", "init", self.confdir])
        # Instance
        self.rev_mgr = RevisionManager()

    def tearDown(self):
        teardown_db()
        shutil.rmtree(self.tmpdir)

    def _run_svn(self, command):
        cmd = ["svn"] + command
        LOGGER.debug('Executing SVN command: %s' % ' '.join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        LOGGER.debug('Output: %r' % (proc.stdout.readlines(), ))

    def test_nochange(self):
        """RevMan: synchronisation sans changement"""
        status = self.rev_mgr.sync()
        expected = {
            "added": [],
            "removed": [],
            'modified': [],
            "toadd": [],
            "toremove": []
        }
        self.assertEqual(status, expected)

    def test_sync_toadd_xml(self):
        """RevMan: synchronisation d'un fichier XML ajouté"""
        newfile = os.path.join(self.confdir, "dummy.xml")
        open(newfile, "w").close()
        status = self.rev_mgr.sync()
        self.assertEqual(status["toadd"], [newfile, ])

    def test_sync_toadd_py(self):
        """RevMan: synchronisation d'un fichier Python ajouté dans le dossier general"""
        newfile = os.path.join(self.confdir, "general", "dummy.py")
        open(newfile, "w").close()
        status = self.rev_mgr.sync()
        self.assertEqual(status["toadd"], [newfile, ])

    def test_sync_toadd_notpy_in_general(self):
        """RevMan: synchronisation d'un fichier non-Python ajouté dans le dossier general"""
        newfile = os.path.join(self.confdir, "general", "dummy")
        open(newfile, "w").close()
        status = self.rev_mgr.sync()
        self.assertEqual(status["toadd"], [])

    def test_sync_toadd_xml_in_general(self):
        """RevMan: synchronisation d'un fichier XML ajouté dans le dossier general"""
        newfile = os.path.join(self.confdir, "general", "dummy.xml")
        open(newfile, "w").close()
        status = self.rev_mgr.sync()
        self.assertEqual(status["toadd"], [])

    def test_sync_toadd_notxml(self):
        """RevMan: synchronisation d'un fichier non-XML ajouté"""
        newfile = os.path.join(self.confdir, "dummy")
        open(newfile, "w").close()
        status = self.rev_mgr.sync()
        self.assertEqual(status["toadd"], [])

    def test_sync_toadd_dir(self):
        """RevMan: synchronisation d'un dossier ajouté"""
        newdir = os.path.join(self.confdir, "dummy")
        os.mkdir(newdir)
        status = self.rev_mgr.sync()
        self.assertEqual(status["toadd"], [newdir, ])

    def test_sync_added(self):
        """RevMan: synchronisation d'un fichier déjà ajouté dans SVN"""
        newfile = os.path.join(self.confdir, "dummy.xml")
        open(newfile, "w").close()
        self._run_svn(["add", newfile])
        status = self.rev_mgr.sync()
        self.assertEqual(status["added"], [newfile, ])
        self.assertEqual(status["toadd"], [])

    def test_sync_missing(self):
        """RevMan: synchronisation d'un fichier supprimé"""
        testfile = os.path.join(self.confdir, "dummy.xml")
        open(testfile, "w").close()
        self._run_svn(["add", testfile])
        self._run_svn(["commit", "-m", "test", self.confdir])
        os.remove(testfile)
        status = self.rev_mgr.sync()
        self.assertEqual(status["toremove"], [testfile, ])
        self.assertEqual(status["removed"], [])

    def test_sync_deleted_xml(self):
        """RevMan: synchronisation d'un fichier supprimé dans SVN"""
        testfile = os.path.join(self.confdir, "dummy.xml")
        open(testfile, "w").close()
        self._run_svn(["add", testfile])
        self._run_svn(["commit", "-m", "test", self.confdir])
        self._run_svn(["rm", testfile])
        status = self.rev_mgr.sync()
        self.assertEqual(status["removed"], [testfile, ])
        self.assertEqual(status["toremove"], [])

    def test_sync_deleted_dir(self):
        """RevMan: synchronisation d'un dossier supprimé dans SVN"""
        testdir = os.path.join(self.confdir, "hosts")
        self._run_svn(["rm", testdir])
        status = self.rev_mgr.sync()
        self.assertEqual(status["removed"], [testdir, ])
        self.assertEqual(status["toremove"], [])

    def test_sync_deleted_dir_and_files(self):
        """RevMan: synchronisation d'un dossier supprimé alors qu'il contenait des fichiers"""
        testdir = os.path.join(self.confdir, "hosts")
        testfile = os.path.join(testdir, "dummy.xml")
        open(testfile, "w").close()
        self._run_svn(["add", testfile])
        self._run_svn(["commit", "-m", "test", self.confdir])
        self._run_svn(["rm", testdir])
        status = self.rev_mgr.sync()
        print status
        self.assertEqual(status["removed"], [testdir, testfile])
        self.assertEqual(status["toremove"], [])

    def test_sync_strange_files(self):
        """RevMan: synchronisation avec un dossier supprimé manuellement contenant des fichiers bizarres"""
        testfile = os.path.join(self.confdir, "dummy.orig.old.disabled")
        open(testfile, "w").close()
        self._run_svn(["add", testfile])
        self._run_svn(["commit", "-m", "test", self.confdir])
        self._run_svn(["rm", testfile])
        status = self.rev_mgr.sync()
        print status
        self.assertEqual(status["toremove"], [])
        self.assertEqual(status["removed"], [testfile])

    def test_sync_moved(self):
        """RevMan: synchronisation d'un fichier renommé"""
        oldname = os.path.join(self.confdir, "dummy1.xml")
        open(oldname, "w").close()
        self._run_svn(["add", oldname])
        self._run_svn(["commit", "-m", "test", self.confdir])
        newname = os.path.join(self.confdir, "dummy2.xml")
        os.rename(oldname, newname)
        status = self.rev_mgr.sync()
        print status
        self.assertEqual(status["toremove"], [oldname, ])
        self.assertEqual(status["removed"], [])
        self.assertEqual(status["toadd"], [newname, ])
        self.assertEqual(status["added"], [])

    def test_sync_modified(self):
        """RevMan: synchronisation d'un fichier modifié"""
        testfile = os.path.join(self.confdir, "dummy.xml")
        open(testfile, "w").close()
        self._run_svn(["add", testfile])
        self._run_svn(["commit", "-m", "test", self.confdir])
        f = open(testfile, "w")
        f.write("dummy\n")
        f.close()
        status = self.rev_mgr.sync()
        print status
        self.assertEqual(status["modified"], [testfile, ])

    def test_sync_no_svnrepository(self):
        """RevMan: synchronisation sans dépôt"""
        settings["vigiconf"]["svnrepository"] = False
        cmdlogger = LoggingCommandFactory(simulate=True)
        self.rev_mgr.command_class = cmdlogger
        self.rev_mgr.sync()
        self.assertEqual(len(cmdlogger.executed), 0)

    def test_sync(self):
        """RevMan: synchronisation"""
        cmdlogger = LoggingCommandFactory(simulate=False)
        self.rev_mgr.command_class = cmdlogger
        # suppression d'un fichier
        test1 = os.path.join(self.confdir, "removed.xml")
        open(test1, "w").close()
        self._run_svn(["add", test1])
        self._run_svn(["commit", "-m", "test", self.confdir])
        os.remove(test1)
        # ajout d'un fichier
        test2 = os.path.join(self.confdir, "added.xml")
        open(test2, "w").close()
        # ajout d'un fichier dans un dossier
        test3 = os.path.join(self.confdir, "addeddir")
        os.mkdir(test3)
        test4 = os.path.join(test3, "added_file_in_dir.xml")
        open(test4, "w").close()
        # on synchronise
        self.rev_mgr.sync()
        expected = [
            ["svn", "status", "--xml", self.confdir],
            self.rev_mgr._get_auth_svn_cmd_prefix("update")
                + ["-r", "HEAD", self.confdir],
            ["svn", "add", test3],
            ["svn", "add", test2],
            ["svn", "remove", test1],
        ]
        print cmdlogger.executed
        # On ne peut pas comparer directement les listes parce que l'ordre des
        # "svn add" peut être différent
        self.assertEqual(len(cmdlogger.executed), len(expected))
        subcommands = [ c[1] for c in cmdlogger.executed ]
        expected_subcommands = [ c[1] for c in expected ]
        self.assertEqual(subcommands, expected_subcommands)
        self.assertEqual(sorted(cmdlogger.executed), sorted(expected))

    def test_sync_manually_deleted_dir(self):
        """RevMan: synchronisation avec un dossier supprimé manuellement"""
        testdir = os.path.join(self.confdir, "hosts")
        testfile = os.path.join(testdir, "dummy.xml")
        open(testfile, "w").close()
        self._run_svn(["add", testfile])
        self._run_svn(["commit", "-m", "test", self.confdir])
        shutil.rmtree(testdir)
        status = self.rev_mgr.sync()
        print status
        self.assertEqual(status["toremove"], [testdir])
        self.assertEqual(status["removed"], [])

    def test_status_no_change(self):
        """RevMan: statut sans changement"""
        DBSession.add(tables.Version(
            name=RevisionManager.version_key,
            version=1
        ))
        DBSession.flush()
        status = self.rev_mgr.status()
        expected = {"added": [], "removed": [], "modified": []}
        self.assertEqual(status, expected)

    def test_status_file_added(self):
        """RevMan: statut après ajout d'un fichier"""
        testdir = os.path.join(self.confdir, "hosts")
        testfile = os.path.join(testdir, "dummy.xml")
        open(testfile, "w").close()
        self._run_svn(["add", testfile])
        self._run_svn(["commit", "-m", "test", self.confdir])
        DBSession.add(tables.Version(
            name=RevisionManager.version_key,
            version=1
        ))
        DBSession.flush()
        status = self.rev_mgr.status()
        expected = {
            "added": [testfile],
            "removed": [],
            "modified": [],
        }
        self.assertEqual(status, expected)

    def test_status_file_deleted(self):
        """RevMan: statut après suppression d'un fichier"""
        testdir = os.path.join(self.confdir, "hosts")
        testfile = os.path.join(testdir, "dummy.xml")
        open(testfile, "w").close()
        self._run_svn(["add", testfile])
        self._run_svn(["commit", "-m", "test", self.confdir])
        self._run_svn(["delete", testfile])
        self._run_svn(["commit", "-m", "test", self.confdir])
        DBSession.add(tables.Version(
            name=RevisionManager.version_key,
            version=2
        ))
        DBSession.flush()
        status = self.rev_mgr.status()
        expected = {
            "added": [],
            "removed": [testfile],
            "modified": [],
        }
        self.assertEqual(status, expected)

    def test_status_file_modified(self):
        """RevMan: statut après modification d'un fichier"""
        testdir = os.path.join(self.confdir, "hosts")
        testfile = os.path.join(testdir, "dummy.xml")
        open(testfile, "w").close()
        self._run_svn(["add", testfile])
        self._run_svn(["commit", "-m", "test", self.confdir])
        fd = open(testfile, "w")
        fd.write("test")
        fd.close()
        self._run_svn(["commit", "-m", "test", self.confdir])
        DBSession.add(tables.Version(
            name=RevisionManager.version_key,
            version=2
        ))
        DBSession.flush()
        status = self.rev_mgr.status()
        expected = {
            "added": [],
            "removed": [],
            "modified": [testfile],
        }
        self.assertEqual(status, expected)

    def test_status_dir_added(self):
        """RevMan: statut après ajout d'un dossier"""
        testdir = os.path.join(self.confdir, "testdir")
        os.mkdir(testdir)
        self._run_svn(["add", testdir])
        self._run_svn(["commit", "-m", "test", self.confdir])
        DBSession.add(tables.Version(
            name=RevisionManager.version_key,
            version=1
        ))
        DBSession.flush()
        status = self.rev_mgr.status()
        expected = {
            "added": [testdir],
            "removed": [],
            "modified": [],
        }
        self.assertEqual(status, expected)

    def test_status_dir_deleted(self):
        """RevMan: statut après suppression d'un dossier"""
        testdir = os.path.join(self.confdir, "hosts")
        testfile = os.path.join(testdir, "dummy.xml")
        open(testfile, "w").close()
        self._run_svn(["add", testfile])
        self._run_svn(["commit", "-m", "test", self.confdir])
        # Nécessaire pour éviter un
        # "SVN warning: Directory 'hosts/' is out of date".
        self._run_svn(["update", self.confdir])
        self._run_svn(["delete", testdir])
        self._run_svn(["commit", "-m", "test2", self.confdir])
        DBSession.add(tables.Version(
            name=RevisionManager.version_key,
            version=2
        ))
        DBSession.flush()
        status = self.rev_mgr.status()
        print status
        expected = {
            "added": [],
            # "svn diff" n'affiche pas les sous-arbres impactés,
            # donc "testfile" n'apparait pas ici.
            "removed": [testdir],
            "modified": [],
        }
        self.assertEqual(status, expected)

    def test_status_dir_changed(self):
        """RevMan: statut d'un dossier après changemement dans le dossier"""
        testdir = os.path.join(self.confdir, "hosts")
        testfile = os.path.join(testdir, "dummy.xml")
        open(testfile, "w").close()
        self._run_svn(["add", testfile])
        self._run_svn(["commit", "-m", "test", self.confdir])
        fd = open(testfile, "w")
        fd.write("test")
        fd.close()
        self._run_svn(["commit", "-m", "test", self.confdir])
        DBSession.add(tables.Version(
            name=RevisionManager.version_key,
            version=2
        ))
        DBSession.flush()
        self.assertEqual(self.rev_mgr.dir_changed(testdir), True)
        self.assertEqual(self.rev_mgr.dir_changed(testdir + os.path.sep), True)
        self.assertEqual(self.rev_mgr.dir_changed(os.path.dirname(testdir)), True)

    def test_status_file_changed(self):
        """RevMan: statut d'un fichier après changemement"""
        testdir = os.path.join(self.confdir, "hosts")
        testfile = os.path.join(testdir, "dummy.xml")
        open(testfile, "w").close()
        self._run_svn(["add", testfile])
        self._run_svn(["commit", "-m", "test", self.confdir])
        fd = open(testfile, "w")
        fd.write("test")
        fd.close()
        self._run_svn(["commit", "-m", "test", self.confdir])
        DBSession.add(tables.Version(
            name=RevisionManager.version_key,
            version=2
        ))
        DBSession.flush()
        self.assertEqual(self.rev_mgr.file_changed(testfile), True)

    def test_status_is_in_dir(self):
        """RevMan: statut de la fonction interne de détection des changements dans les répertoires"""
        self.assertTrue(self.rev_mgr._is_in_dir("/", "/"))
        self.assertTrue(self.rev_mgr._is_in_dir("/", "/a"))
        self.assertTrue(self.rev_mgr._is_in_dir("/", "/a/"))
        self.assertTrue(self.rev_mgr._is_in_dir("/a", "/a"))
        self.assertTrue(self.rev_mgr._is_in_dir("/a", "/a/"))
        self.assertTrue(self.rev_mgr._is_in_dir("/a/", "/a"))
        self.assertTrue(self.rev_mgr._is_in_dir("/a/", "/a/"))
        self.assertTrue(self.rev_mgr._is_in_dir("/a", "/a/b"))
        self.assertTrue(self.rev_mgr._is_in_dir("/a", "/a/b/"))
        self.assertTrue(self.rev_mgr._is_in_dir("/a/", "/a/b"))
        self.assertTrue(self.rev_mgr._is_in_dir("/a/", "/a/b/"))
        self.assertFalse(self.rev_mgr._is_in_dir("/a", "/ab"))
        self.assertFalse(self.rev_mgr._is_in_dir("/a", "/ab/"))
        self.assertFalse(self.rev_mgr._is_in_dir("/a/", "/ab"))
        self.assertFalse(self.rev_mgr._is_in_dir("/a/", "/ab/"))
        self.assertFalse(self.rev_mgr._is_in_dir("/a", "/a.b"))
        self.assertFalse(self.rev_mgr._is_in_dir("/a", "/a.b/"))
        self.assertFalse(self.rev_mgr._is_in_dir("/a/", "/a.b"))
        self.assertFalse(self.rev_mgr._is_in_dir("/a/", "/a.b/"))
