# -*- coding: utf-8 -*-
"""
Test de l'application connector-metro
"""

import os
import shutil
import unittest

#from vigilo.common.conf import settings

from vigilo.vigiconf.applications.connector_metro import ConnectorMetro
import vigilo.vigiconf.conf as conf
from vigilo.vigiconf.lib.confclasses.host import Host
from vigilo.vigiconf.lib.server.local import ServerLocal

from helpers import setup_tmpdir


class ConnectorMetroTest(unittest.TestCase):

    def setUp(self):
        self.tmpdir = setup_tmpdir()
        self.basedir = os.path.join(self.tmpdir, "deploy")
        self.host = Host(conf.hostsConf, "dummy.xml", "testserver1",
                         "192.168.1.1", "Servers")
        self.host.add_perfdata_handler("dummy", "dummy", "dummy", "dummy")

    def tearDown(self):
        """Call after every test case."""
        shutil.rmtree(self.tmpdir)

    def test_add_missing_servers(self):
        app = ConnectorMetro()
        ventilation = {"testserver1":
                {"connector-metro": "localhost"}
            }
        app.generate(ventilation)
        self.assertTrue("localhost" in app.servers)
        self.assertEqual(app.servers["localhost"].name, "localhost")
        self.assertEqual(app.actions, {"localhost": ["stop", "start"]})