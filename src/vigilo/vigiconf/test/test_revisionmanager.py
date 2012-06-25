# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# pylint: disable-msg=C0111,W0212,R0904
# Copyright (C) 2006-2012 CS-SI
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

from vigilo.vigiconf.lib.dispatchator.revisionmanager import RevisionManager

from .helpers import setup_tmpdir, LoggingCommandFactory


class RevisionManagerTest(unittest.TestCase):

    def setUp(self):
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
        shutil.rmtree(self.tmpdir)

    def _run_svn(self, command):
        devnull = open(os.devnull, "w")
        subprocess.call(["svn"] + command, stdout=devnull,
                        stderr=subprocess.STDOUT)
        devnull.close()

    def test_nochange(self):
        """RevMan: aucun changement"""
        status = self.rev_mgr.status()
        expected = {"toadd": [], "added": [],
                    "toremove": [], "removed": [], 'modified': []}
        self.assertEqual(status, expected)

    def test_status_toadd_xml(self):
        """RevMan: fichier XML ajouté"""
        newfile = os.path.join(self.confdir, "dummy.xml")
        open(newfile, "w").close()
        status = self.rev_mgr.status()
        self.assertEqual(status["toadd"], [newfile, ])

    def test_status_toadd_py(self):
        """RevMan: fichier Python ajouté dans le dossier general"""
        newfile = os.path.join(self.confdir, "general", "dummy.py")
        open(newfile, "w").close()
        status = self.rev_mgr.status()
        self.assertEqual(status["toadd"], [newfile, ])

    def test_status_toadd_notpy_in_general(self):
        """RevMan: fichier non-Python ajouté dans le dossier general"""
        newfile = os.path.join(self.confdir, "general", "dummy")
        open(newfile, "w").close()
        status = self.rev_mgr.status()
        self.assertEqual(status["toadd"], [])

    def test_status_toadd_xml_in_general(self):
        """RevMan: fichier XML ajouté dans le dossier general"""
        newfile = os.path.join(self.confdir, "general", "dummy.xml")
        open(newfile, "w").close()
        status = self.rev_mgr.status()
        self.assertEqual(status["toadd"], [])

    def test_status_toadd_notxml(self):
        """RevMan: fichier non-XML ajouté"""
        newfile = os.path.join(self.confdir, "dummy")
        open(newfile, "w").close()
        status = self.rev_mgr.status()
        self.assertEqual(status["toadd"], [])

    def test_status_toadd_dir(self):
        """RevMan: dossier ajouté"""
        newdir = os.path.join(self.confdir, "dummy")
        os.mkdir(newdir)
        status = self.rev_mgr.status()
        self.assertEqual(status["toadd"], [newdir, ])

    def test_status_added(self):
        """RevMan: fichier déjà ajouté dans SVN"""
        newfile = os.path.join(self.confdir, "dummy.xml")
        open(newfile, "w").close()
        self._run_svn(["add", newfile])
        status = self.rev_mgr.status()
        self.assertEqual(status["added"], [newfile, ])
        self.assertEqual(status["toadd"], [])

    def test_status_missing(self):
        """RevMan: fichier supprimé"""
        testfile = os.path.join(self.confdir, "dummy.xml")
        open(testfile, "w").close()
        self._run_svn(["add", testfile])
        self._run_svn(["commit", "-m", "test", self.confdir])
        os.remove(testfile)
        status = self.rev_mgr.status()
        self.assertEqual(status["toremove"], [testfile, ])
        self.assertEqual(status["removed"], [])

    def test_status_deleted_xml(self):
        """RevMan: fichier supprimé dans SVN"""
        testfile = os.path.join(self.confdir, "dummy.xml")
        open(testfile, "w").close()
        self._run_svn(["add", testfile])
        self._run_svn(["commit", "-m", "test", self.confdir])
        self._run_svn(["rm", testfile])
        status = self.rev_mgr.status()
        self.assertEqual(status["removed"], [testfile, ])
        self.assertEqual(status["toremove"], [])

    def test_status_deleted_dir(self):
        """RevMan: dossier supprimé dans SVN"""
        testdir = os.path.join(self.confdir, "hosts")
        self._run_svn(["rm", testdir])
        status = self.rev_mgr.status()
        self.assertEqual(status["removed"], [testdir, ])
        self.assertEqual(status["toremove"], [])

    def test_status_deleted_dir_and_files(self):
        """RevMan: dossier supprimé alors qu'il contenait des fichiers"""
        testdir = os.path.join(self.confdir, "hosts")
        testfile = os.path.join(testdir, "dummy.xml")
        open(testfile, "w").close()
        self._run_svn(["add", testfile])
        self._run_svn(["commit", "-m", "test", self.confdir])
        self._run_svn(["rm", testdir])
        status = self.rev_mgr.status()
        print status
        self.assertEqual(status["removed"], [testdir, testfile])
        self.assertEqual(status["toremove"], [])

    def test_status_strange_files(self):
        """RevMan: synchronisation avec un dossier supprimé manuellement contenant des fichiers bizarres"""
        testfile = os.path.join(self.confdir, "dummy.orig.old.disabled")
        open(testfile, "w").close()
        self._run_svn(["add", testfile])
        self._run_svn(["commit", "-m", "test", self.confdir])
        self._run_svn(["rm", testfile])
        status = self.rev_mgr.status()
        print status
        self.assertEqual(status["toremove"], [])
        self.assertEqual(status["removed"], [testfile])

    def test_status_moved(self):
        """RevMan: fichier renommé"""
        oldname = os.path.join(self.confdir, "dummy1.xml")
        open(oldname, "w").close()
        self._run_svn(["add", oldname])
        self._run_svn(["commit", "-m", "test", self.confdir])
        newname = os.path.join(self.confdir, "dummy2.xml")
        os.rename(oldname, newname)
        status = self.rev_mgr.status()
        print status
        self.assertEqual(status["toremove"], [oldname, ])
        self.assertEqual(status["removed"], [])
        self.assertEqual(status["toadd"], [newname, ])
        self.assertEqual(status["added"], [])

    def test_status_modified(self):
        """RevMan: fichier modifié"""
        testfile = os.path.join(self.confdir, "dummy.xml")
        open(testfile, "w").close()
        self._run_svn(["add", testfile])
        self._run_svn(["commit", "-m", "test", self.confdir])
        f = open(testfile, "w")
        f.write("dummy\n")
        f.close()
        status = self.rev_mgr.status()
        print status
        self.assertEqual(status["modified"], [testfile, ])

    def test_sync_no_svnrepository(self):
        """RevMan: demande de synchro sans dépôt"""
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
            ["svn", "add", test3],
            ["svn", "add", test2],
            self.rev_mgr._get_auth_svn_cmd_prefix("update")
                + ["-r", "HEAD", self.confdir],
            ["svn", "remove", test1],
            ["svn", "status", "--xml", self.confdir],
        ]
        print cmdlogger.executed
        # On ne peut pas comparer directement les listes parce que l'ordre des
        # "svn add" peut être différent
        self.assertEqual(len(cmdlogger.executed), len(expected))
        subcommands = [ c[1] for c in cmdlogger.executed ]
        expected_subcommands = [ c[1] for c in expected ]
        self.assertEqual(subcommands, expected_subcommands)
        self.assertEqual(sorted(cmdlogger.executed), sorted(expected))
        status = self.rev_mgr.status()
        print status
        # Là aussi, l'ordre n'est pas garanti
        status["added"].sort()
        expected = {'toremove': [],
                    'removed': [test1, ],
                    'added': [test2, test3, test4],
                    'toadd': [],
                    'modified': []}
        expected["added"].sort()
        self.assertEqual(status, expected)

    def test_sync_manually_deleted_dir(self):
        """RevMan: synchronisation avec un dossier supprimé manuellement"""
        testdir = os.path.join(self.confdir, "hosts")
        testfile = os.path.join(testdir, "dummy.xml")
        open(testfile, "w").close()
        self._run_svn(["add", testfile])
        self._run_svn(["commit", "-m", "test", self.confdir])
        shutil.rmtree(testdir)
        self.rev_mgr.sync()
        status = self.rev_mgr.status()
        print status
        self.assertEqual(status["removed"], [testdir, testfile])
        self.assertEqual(status["toremove"], [])
