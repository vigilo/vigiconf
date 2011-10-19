# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# pylint: disable-msg=C0111,W0212,R0904
# Copyright (C) 2011-2011 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

import os
import unittest
import shutil
import re
from subprocess import Popen, PIPE, STDOUT

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
from vigilo.vigiconf.applications import collector

from helpers import setup_tmpdir, DummyRevMan
from helpers import setup_db, teardown_db


class CollectorGeneratorTestCase(unittest.TestCase):

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
        self.collector = collector.Collector()
        self.genmanager = GeneratorManager([self.collector])

    def tearDown(self):
        DBSession.expunge_all()
        teardown_db()
        shutil.rmtree(self.tmpdir)
        settings["vigiconf"]["confdir"] = self.old_conf_path

    def _validate(self):
        self.genmanager.generate(DummyRevMan())
        deploydir = os.path.join(self.basedir, "localhost")
        conffile = os.path.join(deploydir, "collector", "testserver1.pm")
        self.assertTrue(os.path.exists(conffile))
        validation_script = os.path.join(os.path.dirname(collector.__file__),
                                         "validate.sh")
        proc = Popen(["sh", validation_script, deploydir],
                    stdout=PIPE, stderr=STDOUT)
        print proc.communicate()[0]
        self.assertEqual(proc.returncode, 0)

    def test_basic(self):
        """Collector: fonctionnement nominal"""
        test_list = self.testfactory.get_test("Interface", self.host.classes)
        self.host.add_tests(test_list, {"label":"eth0", "ifname":"eth0"})
        self._validate()

    def test_unicode(self):
        """Collector: caractères unicode"""
        test_list = self.testfactory.get_test("Interface", self.host.classes)
        self.host.add_tests(test_list, {"label":u"aàeéècç", "ifname":u"aàeéècç"})
        self._validate()

