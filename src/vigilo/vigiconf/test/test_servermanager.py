# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# pylint: disable-msg=C0111,W0212,R0904
# Copyright (C) 2006-2016 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Test de l'objet ServerManager
"""

import unittest

from mock import Mock

from vigilo.vigiconf.lib.server.manager import ServerManager


class ServerManagerTest(unittest.TestCase):

    def setUp(self):
        srv1 = Mock(name="server1")
        srv1.testMethod.return_value = True
        srv2 = Mock(name="server2")
        srv2.testMethod.return_value = False
        self.srvmgr = ServerManager(None)
        self.srvmgr.servers = {"server1": srv1, "server2": srv2}

    def test_filter_servers(self):
        filtered = self.srvmgr.filter_servers("testMethod")
        self.assertEqual(filtered, ["server1", ])

    def test_filter_servers_force(self):
        filtered = self.srvmgr.filter_servers("testMethod",
                                              force=("deploy", ))
        self.assertEqual(filtered, ["server1", "server2"])

