# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# pylint: disable-msg=C0111,W0212,R0904
# Copyright (C) 2006-2013 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Test de l'application connector-metro
"""
from __future__ import absolute_import

import os
import shutil
import unittest
import sqlite3

from vigilo.vigiconf.applications.connector_metro import ConnectorMetro
import vigilo.vigiconf.conf as conf
from vigilo.vigiconf.lib.confclasses.host import Host

from .helpers import setup_tmpdir


class ConnectorMetroTest(unittest.TestCase):

    def setUp(self):
        self.tmpdir = setup_tmpdir()
        self.basedir = os.path.join(self.tmpdir, "deploy")
        self.host = Host(conf.hostsConf, "dummy.xml", "testserver1",
                         "192.168.1.1", "Servers")
        self.host.add_perfdata("dummy", "dummy")

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

    def test_generated(self):
        app = ConnectorMetro()
        ventilation = {"testserver1":
                {"connector-metro": "localhost"}
            }
        app.generate(ventilation)
        db_path = os.path.join(self.basedir, "localhost",
                               "connector-metro.db")
        self.assertTrue(os.path.exists(db_path))
        db = sqlite3.connect(db_path)
        cur = db.cursor()
        cur.execute("SELECT * FROM perfdatasource")
        pds = cur.fetchall()
        cur.execute("SELECT * FROM rra")
        rra = cur.fetchall()
        cur.execute("SELECT * FROM pdsrra")
        pdsrra = cur.fetchall()
        cur.close()
        db.close()
        self.assertEqual(pds, [
            (1, 'dummy', 'testserver1', 'GAUGE', 300, 600, None,
             None, 1.0, None, None, None, u'localhost') ])
        self.assertEqual(rra, [
            (1, 'AVERAGE', 0.5, 1, 600),  (2, 'AVERAGE', 0.5, 6,   700),
            (3, 'AVERAGE', 0.5, 24, 775), (4, 'AVERAGE', 0.5, 288, 732)
            ])
        self.assertEqual(pdsrra, [
            (1, 1, 0),
            (1, 2, 1),
            (1, 3, 2),
            (1, 4, 3),
            ])
