# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# pylint: disable-msg=C0111,W0212,R0904
# Copyright (C) 2006-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Test that the dispatchator works properly
"""

import os
import locale
import unittest

from vigilo.common.conf import settings

import vigilo.vigiconf.conf as conf
from vigilo.vigiconf.lib.confclasses.host import Host
from vigilo.vigiconf.lib.confclasses.test import TestFactory
from vigilo.vigiconf.lib.dispatchator import make_dispatchator

from helpers import setup_tmpdir, DummyCommand
from helpers import setup_deploy_dir, teardown_deploy_dir
from helpers import setup_db, teardown_db


class DispatchatorTest(unittest.TestCase):

    def setUp(self):
        setup_db()
        self.tmpdir = setup_tmpdir()
        self.old_conf_path = settings["vigiconf"]["confdir"]
        settings["vigiconf"]["confdir"] = os.path.join(self.tmpdir, "conf.d")
        os.mkdir(settings["vigiconf"]["confdir"])

        # Prepare necessary directories
        # TODO: commenter les divers repertoires
        setup_deploy_dir()
        self.host = Host(conf.hostsConf, "dummy", u"testserver1",
                         u"192.168.1.1", u"Servers")
        testfactory = TestFactory(confdir=settings["vigiconf"]["confdir"])
        test_list = testfactory.get_test("UpTime", self.host.classes)
        self.host.add_tests(test_list)
        self.dispatchator = make_dispatchator()
        # Disable qualification, validation, stop and start scripts
        for app in self.dispatchator.apps_mgr.applications:
            app.validation = None
            app.start_command = None
            app.stop_command = None
        # Don't check the installed revisions
        self.dispatchator.force = ("deploy", "db-sync")

    def tearDown(self):
        teardown_db()
        teardown_deploy_dir()
        settings["vigiconf"]["confdir"] = self.old_conf_path

    def test_deploy(self):
        """Globally test the deployment"""
        self.dispatchator.deploy()

    def test_restart(self):
        """Globally test the restart"""
        # Create necessary file
        revs = open(os.path.join(conf.baseConfDir, "new", "revisions.txt"), "w")
        revs.close()
        self.dispatchator.restart()

    def test_conf_reactivation(self):
        """ Test de réactivation d'une conf versionnée.
        Chaque configuration doit être mise en version et doit pouvoir être
        réactivée par passage d'une commande particulière.
        VIGILO_EXIG_VIGILO_CONFIGURATION_0020
        """
        settings["vigiconf"]["svnusername"] = "user1"
        settings["vigiconf"]["svnpassword"] = "pass1"
        rev_mgr = self.dispatchator.rev_mgr
        rev_mgr.deploy_revision = 1234
        rev_mgr.command_class = DummyCommand
        svn_cmd = rev_mgr.update()

        self.assertEquals(svn_cmd,
                    ["svn", "update", "--username", "user1",
                     "--password", "pass1", "-r", "1234",
                     settings["vigiconf"]["confdir"]],
                    "Invalid svn update command")

    def test_get_state(self):
        """Test de la récupération de l'état (par la commande vigiconf info)"""
        locale.setlocale(locale.LC_ALL, 'C')
        self.dispatchator.rev_mgr.last_revision = lambda: 43
        state = self.dispatchator.getState()
        print state
        self.assertEqual(len(state), 2)
