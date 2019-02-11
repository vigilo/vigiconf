# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# pylint: disable-msg=C0111,W0212,R0904
# Copyright (C) 2006-2019 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Tests de génération de configuration pour VigiRRD
"""
from __future__ import absolute_import

import os
import unittest
import shutil
import sqlite3

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib.confclasses.host import Host
from vigilo.vigiconf.applications.vigirrd import VigiRRD

from .helpers import setup_tmpdir


class VigiRRDTest(unittest.TestCase):

    def setUp(self):
        conf.load_general_conf() # Réinitialisation de la configuration
        self.tmpdir = setup_tmpdir()
        os.mkdir(os.path.join(self.tmpdir, "deploy"))
        self.host = Host(conf.hostsConf, "dummy.xml", "testserver1",
                         "192.168.1.1", "Servers")
        self.vigirrd = VigiRRD()
        ventilation = {"testserver1": {"vigirrd": "sup.example.com"}}
        self.generator = self.vigirrd.generator(self.vigirrd, ventilation)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_graph_order(self):
        for i in range(7):
            self.host.add_perfdata("test_ds_%d" % i, "dummy")
        self.host.add_graph("test graph 1",
                [ "test_ds_%d" % i for i in range(7) ],
                "lines", "dummy")
        self.host.add_graph("test graph 2",
                [ "test_ds_%d" % i for i in range(6, -1, -1) ],
                "lines", "dummy")
        self.generator.generate()
        db = sqlite3.connect(os.path.join(self.tmpdir, "deploy",
                                          "sup.example.com", "vigirrd.db"))
        c = db.cursor()
        c.execute("""SELECT pds.name FROM perfdatasource pds
                     JOIN graphperfdatasource gpds
                       ON pds.idperfdatasource = gpds.idperfdatasource
                     JOIN graph g
                       ON g.idgraph = gpds.idgraph
                     WHERE g.name = ? ORDER BY gpds.`order`""",
                  ("test graph 1", ))
        ds_in_graph_1 = [ r[0] for r in c.fetchall() ]
        self.assertEqual(ds_in_graph_1, [ "test_ds_%d" % i for i in range(7) ])
        c.execute("""SELECT pds.name FROM perfdatasource pds
                     JOIN graphperfdatasource gpds
                       ON pds.idperfdatasource = gpds.idperfdatasource
                     JOIN graph g
                       ON g.idgraph = gpds.idgraph
                     WHERE g.name = ? ORDER BY gpds.`order`""",
                  ("test graph 2", ))
        ds_in_graph_2 = [ r[0] for r in c.fetchall() ]
        self.assertEqual(ds_in_graph_2,
                         [ "test_ds_%d" % i for i in range(6, -1, -1) ])
