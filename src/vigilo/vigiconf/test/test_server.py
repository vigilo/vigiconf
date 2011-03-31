# -*- coding: utf-8 -*-
"""
Test de l'objet Server
"""

import os
import shutil
import unittest

from vigilo.common.conf import settings

import vigilo.vigiconf.conf as conf
from vigilo.vigiconf.lib.server.local import ServerLocal

from helpers import setup_tmpdir, LoggingCommand
from helpers import setup_db, teardown_db


class ServerFakeCommand(ServerLocal):
    def __init__(self, name):
        ServerLocal.__init__(self, name)
        self.executed = []
        self.command_result = ""
    def createCommand(self, command):
        return LoggingCommand(command, self.executed, self.command_result)

class ServerTest(unittest.TestCase):

    def setUp(self):
        setup_db()
        self.tmpdir = setup_tmpdir()
        settings["vigiconf"]["confdir"] = os.path.join(self.tmpdir, "conf.d")
        os.mkdir(settings["vigiconf"]["confdir"])
        self.server = ServerFakeCommand("testserver")

    def tearDown(self):
        """Call after every test case."""
        teardown_db()
        shutil.rmtree(self.tmpdir)


    def test_update_revisions(self):
        self.server.command_result = "new 42\nprod 41\nold 40\n"
        self.server.update_revisions()
        self.assertEqual(self.server.executed, [['vigiconf-local', 'get-revisions'], ])
        self.assertEqual(self.server.revisions,
                         {"deployed": 42,
                          "installed": 41,
                          "previous": 40,
                          "conf": None,
                         })

    def test_get_state_text(self):
        """Test de la récupération de l'état sous forme de texte"""
        self.server.command_result = "new 42\nprod 41\nold 40\n"
        state = self.server.get_state_text(43)
        # On ne peut pas tester directement à cause de la traduction
        self.assertEqual(state.count("40"), 1)
        self.assertEqual(state.count("41"), 1)
        self.assertEqual(state.count("42"), 1)
        self.assertEqual(state.count("->"), 1)
        self.assertEqual(state.count(","), 1)

    def test_get_state_text_disabled(self):
        """
        Si le serveur est désactivé, son état doit contenir le message
        correspondant
        """
        self.server.is_enabled = lambda: False
        state = self.server.get_state_text(0)
        print state
        # On ne peut pas tester directement à cause de la traduction
        self.assertEqual(state.count("\n"), 4)

