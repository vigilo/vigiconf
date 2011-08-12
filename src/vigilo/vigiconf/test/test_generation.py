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
        add_host("testserver2")
        # Try the generation
        self.genmanager.generate(DummyRevMan())

    def test_add_metro_service_nagios(self):
        """Test for the add_metro_service method"""
        test_list = self.testfactory.get_test("Interface", self.host.classes)
        self.host.add_tests(test_list, {"label":"eth1", "ifname":"eth1"})
        self.host.add_metro_service("Traffic in eth1", "ineth1", 10, 20)
        self.genmanager.generate(DummyRevMan())
        nagiosconf = os.path.join(self.basedir, "localhost",
                                  "nagios", "nagios.cfg")
        self.assert_(os.path.exists(nagiosconf),
                     "Nagios conf file was not generated")
        nagios = open(nagiosconf).read()

        regexp_coll = re.compile(r"""
            define\s+service\s*\{\s*                # Inside an service definition
                use\s+generic-active-service\s*
                host_name\s+testserver1\s*
                service_description\s+Collector\s*
                check_command\s+Collector\s*
                [^\}]+                              # Any following declaration
                \}                                  # End of the host definition
            """,
            re.MULTILINE | re.VERBOSE)

        regexp_svc = re.compile(r"""
            define\s+service\s*\{\s*                # Inside an service definition
                use\s+generic-active-service\s*
                host_name\s+testserver1\s*          # Working on the testserver1 host
                service_description\s+Traffic[ ]in[ ]eth1\s*
                check_command\s+report_stale_data\s*
                max_check_attempts\s+3\s*
                freshness_threshold\s+\d+\s*
                check_freshness\s+1\s*
                active_checks_enabled\s+0\s*
                passive_checks_enabled\s+1\s*
                [^\}]+                              # Any following declaration
                \}                                  # End of the host definition
            """,
            re.MULTILINE | re.VERBOSE)
        print nagios
        self.assert_(regexp_coll.search(nagios) is not None,
            "add_metro_service does not generate proper nagios conf "
            "(Collector service)")
        self.assert_(regexp_svc.search(nagios) is not None,
            "add_metro_service does not generate proper nagios conf "
            "(passive service)")


class NagiosGeneratorForTest(NagiosGen):
    def templateAppend(self, filename, template, args):
        """Redefinition pour tester les directives generiques nagios"""
        if args.has_key('generic_directives'):
            self.test_host_data = args
        elif args.has_key('generic_sdirectives'):
            if args['generic_sdirectives'] != "":
                self.test_srv_data = args
        super(NagiosGeneratorForTest, self).templateAppend(filename,
                template, args)


class TestGenericDirNagiosGeneration(unittest.TestCase):

    def setUp(self):
        # Prepare temporary directory
        self.tmpdir = setup_tmpdir()
        self.basedir = os.path.join(self.tmpdir, "deploy")
        # on charge en conf un host avec directives generiques nagios
        setup_db()
        self.host = Host(conf.hostsConf, "dummy.xml", "testserver1",
                         "192.168.1.1", "Servers")
        add_host("testserver1", ConfFile.get_or_create("dummy.xml"))
        self.apps = {"nagios": Nagios(), "vigimap": VigiMap(),
                     "connector-metro": ConnectorMetro()}
        self.ventilation = {"testserver1": {}}
        for appname in self.apps:
            self.ventilation["testserver1"][appname] = "sup.example.com"

    def tearDown(self):
        DBSession.expunge_all()
        teardown_db()
        shutil.rmtree(self.tmpdir)

    def test_nagios_directives(self):
        self.host.add_nagios_directive("max_check_attempts", "5")
        self.host.add_nagios_directive("check_interval", "10")
        self.host.add_nagios_directive("retry_interval", "1")

        self.apps["nagios"].generate(self.ventilation)
        nagiosconffile = os.path.join(self.basedir, "sup.example.com",
                                      "nagios", "nagios.cfg")
        self.assert_(os.path.exists(nagiosconffile),
                     "Nagios conf file was not generated")
        nagiosconf = open(nagiosconffile).read()
        print nagiosconf

        self.assertTrue("max_check_attempts    5" in nagiosconf,
            "nagios generator generates max_check_attempts=5")

        self.assertTrue("check_interval    10" in nagiosconf,
            "nagios generator generates check_interval=10")

        self.assertTrue("retry_interval    1" in nagiosconf,
            "nagios generator generates retry_interval=1")

    def test_nagios_service_directives(self):
        self.host.add_external_sup_service("testservice")
        self.host.add_nagios_service_directive(
                "testservice", "max_check_attempts", "6")
        self.host.add_nagios_service_directive(
                "testservice", "check_interval", "11")
        self.host.add_nagios_service_directive(
                "testservice", "retry_interval", "2")

        self.apps["nagios"].generate(self.ventilation)
        nagiosconffile = os.path.join(self.basedir, "sup.example.com",
                                      "nagios", "nagios.cfg")
        self.assert_(os.path.exists(nagiosconffile),
                     "Nagios conf file was not generated")
        nagiosconf = open(nagiosconffile).read()
        print nagiosconf

        self.assertTrue("max_check_attempts    6" in nagiosconf,
            "nagios generator generates max_check_attempts=6")

        self.assertTrue("check_interval    11" in nagiosconf,
            "nagios generator generates check_interval=11")

        self.assertTrue("retry_interval    2" in nagiosconf,
            "nagios generator generates retry_interval=2")

    def test_parents_directive(self):
        # On ajoute un 2ème hôte et on génère une dépendance topologique
        # de "testserver1" sur "testserver2".
        add_host("testserver2", ConfFile.get_or_create("dummy.xml"))
        self.ventilation.update({"testserver2": {}})
        for appname in self.apps:
            self.ventilation["testserver2"][appname] = "sup.example.com"
        dep_group = add_dependency_group('testserver1', None, 'topology')
        add_dependency(dep_group, ("testserver2", None))
        vserver = add_vigiloserver("sup.example.com")
        nagios = add_application("nagios")
        add_ventilation("testserver1", vserver, nagios)
        add_ventilation("testserver2", vserver, nagios)

        # "testserver2" doit apparaître comme parent de "testserver1"
        # dans le fichier de configuration généré pour Nagios.
        self.apps["nagios"].generate(self.ventilation)
        nagiosconffile = os.path.join(self.basedir, "sup.example.com",
                                      "nagios", "nagios.cfg")
        self.assert_(os.path.exists(nagiosconffile),
                     "Nagios conf file was not generated")
        nagiosconf = open(nagiosconffile).read()
        print nagiosconf

        self.assertTrue("parents    testserver2" in nagiosconf,
            "nagios generator generates did not add the proper parents")

