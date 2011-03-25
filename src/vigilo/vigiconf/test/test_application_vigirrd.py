#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests de génération de configuration pour VigiRRD
"""

import os
import unittest
import shutil
import sqlite3

from vigilo.common.conf import settings
from vigilo.models import tables
from vigilo.models.demo import functions as df
from vigilo.models.session import DBSession

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib.confclasses.host import Host
from vigilo.vigiconf.applications.vigirrd import VigiRRD

from helpers import setup_tmpdir


class VigiRRDTest(unittest.TestCase):

    def setUp(self):
        self.tmpdir = setup_tmpdir()
        os.mkdir(os.path.join(self.tmpdir, "deploy"))
        self.host = Host(conf.hostsConf, "dummy.xml", "testserver1",
                         "192.168.1.1", "Servers")
        self.vigirrd = VigiRRD()
        ventilation = {"testserver1": {"vigirrd": "sup.example.com"}}
        self.generator = self.vigirrd.generator(self.vigirrd, ventilation)

    def tearDown(self):
        conf.hostfactory.hosts = {}
        conf.hostsConf = conf.hostfactory.hosts
        shutil.rmtree(self.tmpdir)

    def test_graph_order(self):
        for i in range(7):
            self.host.add_perfdata_handler("dummy_service", "test_ds_%d" % i,
                    "test_ds_label_%d" % i, "test_ds_%d" % i)
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
