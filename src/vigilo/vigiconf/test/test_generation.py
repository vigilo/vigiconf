# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# pylint: disable-msg=C0111,W0212,R0904
# Copyright (C) 2006-2011 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

import os
import unittest
import shutil
import re

from vigilo.common.conf import settings
from vigilo.models.tables import ConfFile
from vigilo.models.demo.functions import add_host, add_dependency_group, \
                                            add_dependency, add_vigiloserver, \
                                            add_application, add_ventilation
from vigilo.models.session import DBSession

import vigilo.vigiconf.conf as conf
from vigilo.vigiconf.lib.generators import GeneratorManager
from vigilo.vigiconf.lib.confclasses.host import Host
from vigilo.vigiconf.lib.confclasses.test import TestFactory
from vigilo.vigiconf.applications.nagios import Nagios
from vigilo.vigiconf.applications.vigimap import VigiMap
from vigilo.vigiconf.applications.connector_metro import ConnectorMetro
from vigilo.vigiconf.applications.nagios.generator import NagiosGen

from helpers import setup_tmpdir, DummyRevMan
from helpers import setup_db, teardown_db


class Generator(unittest.TestCase):

    def setUp(self):
        setup_db()
        # Prepare temporary directory
        self.tmpdir = setup_tmpdir()
        self.basedir = os.path.join(self.tmpdir, "deploy")
        self.old_conf_path = settings["vigiconf"]["confdir"]
        settings["vigiconf"]["confdir"] = os.path.join(self.tmpdir, "conf.d")
        os.mkdir(settings["vigiconf"]["confdir"])
        self.testfactory = TestFactory(confdir=settings["vigiconf"]["confdir"])
        self.host = Host(conf.hostsConf, "dummy.xml", "testserver1",
                         "192.168.1.1", "Servers")
        # attention, le fichier dummy.xml doit exister ou l'hôte sera supprimé
        # juste après avoir été inséré
        open(os.path.join(self.tmpdir, "conf.d", "dummy.xml"), "w").close()
        conffile = ConfFile.get_or_create("dummy.xml")
        add_host("testserver1", conffile)
        add_host("localhost", conffile)
        add_host("localhost2", conffile)
        Host(conf.hostsConf, "dummy.xml", "localhost2", "127.0.0.1", "Servers")
        self.apps = {"nagios": Nagios(), "vigimap": VigiMap(),
                     "connector-metro": ConnectorMetro()}
        self.genmanager = GeneratorManager(self.apps.values())

    def tearDown(self):
        DBSession.expunge_all()
        teardown_db()
        shutil.rmtree(self.tmpdir)
        settings["vigiconf"]["confdir"] = self.old_conf_path

    def test_generation(self):
        """Globally test the generation"""
        # Fill with random definitions...
        test_list = self.testfactory.get_test("Interface", self.host.classes)
        self.host.add_tests(test_list, {"label":"eth1", "ifname":"eth1"})
        self.host.add_metro_service("Traffic in eth1", "ineth1", 10, 20)
        self.host.add_collector_metro("TestAddCS", "TestAddCSMFunction",
                            ["fake arg 1"], ["GET/.1.3.6.1.2.1.1.3.0"],
                            "GAUGE", label="TestAddCSLabel")
        host2 = Host(conf.hostsConf, "host/localhost.xml", u"testserver2",
                     "192.168.1.2", "Servers")
        host2.add_collector_service( u"TestAddCSReRoute",
                "TestAddCSReRouteFunction",
                ["fake arg 1"], ["GET/.1.3.6.1.2.1.1.3.0"],
                reroutefor={'host': "testserver1",
                            "service": u"TestAddCSReRoute"} )
        conffile = ConfFile.get_or_create("dummy.xml")
        add_host("testserver2", conffile)
        # Try the generation
        self.genmanager.generate(DummyRevMan())

    def test_generation_relative_group(self):
        """Les groupes 'relatifs' sont correctement gérés (#829)."""
        os.mkdir(os.path.join(self.tmpdir, "conf.d", "groups"))
        f = open(os.path.join(self.tmpdir, "conf.d", "groups", "dummy.xml"), "w")
        f.write('<?xml version="1.0"?><groups><group name="Vigilo"/></groups>')
        f.close()
        self.host.add_group('Vigilo')
        self.genmanager.generate(DummyRevMan())

