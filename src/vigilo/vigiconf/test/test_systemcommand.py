# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# pylint: disable-msg=C0111,W0212,R0904
# Copyright (C) 2006-2011 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Tests sur l'exécuteur de commandes (SystemCommand)
"""

import os
import subprocess
import unittest

from vigilo.common.conf import settings

from vigilo.vigiconf.lib.systemcommand import SystemCommand
from vigilo.vigiconf.lib.systemcommand import SystemCommandError
from vigilo.vigiconf.lib.systemcommand import MissingCommand


class SystemCommandTest(unittest.TestCase):

    def test_missing_command(self):
        """
        SystemCommand: commande inexistante -> exception
        """
        s = SystemCommand(["non-existant-command", ])
        self.assertRaises(MissingCommand, s.execute)
        s = SystemCommand("non-existant-command")
        self.assertRaises(MissingCommand, s.execute)

    def test_failing_command(self):
        """
        SystemCommand: commande qui échoue -> exception
        """
        s = SystemCommand("false")
        self.assertRaises(SystemCommandError, s.execute)
        s = SystemCommand(["false", ])
        self.assertRaises(SystemCommandError, s.execute)

