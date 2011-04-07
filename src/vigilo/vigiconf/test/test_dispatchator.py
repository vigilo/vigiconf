# -*- coding: utf-8 -*-
"""
Test that the dispatchator works properly
"""

import os
import locale
import unittest

from vigilo.common.conf import settings

import vigilo.vigiconf.conf as conf
from vigilo.vigiconf.lib.confclasses.host import Host
from vigilo.vigiconf.lib.dispatchator import make_dispatchator

from helpers import setup_tmpdir, DummyCommand
from helpers import setup_deploy_dir, teardown_deploy_dir
from helpers import setup_db, teardown_db

#pylint: disable-msg=C0111


class DispatchatorTest(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
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
        test_list = conf.testfactory.get_test("UpTime", self.host.classes)
        self.host.add_tests(test_list)
        self.dispatchator = make_dispatchator()
        # Disable qualification, validation, stop and start scripts
        for app in self.dispatchator.apps_mgr.applications:
            app.validation = None
            app.start_command = None
            app.stop_command = None
        # Don't check the installed revisions
        self.dispatchator.force = True

    def tearDown(self):
        """Call after every test case."""
        conf.hostfactory.hosts = {}
        conf.hostsConf = conf.hostfactory.hosts
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


# vim:set expandtab tabstop=4 shiftwidth=4:
