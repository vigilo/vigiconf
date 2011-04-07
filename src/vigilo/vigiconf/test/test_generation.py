#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test that the generation works properly
"""

import os
import unittest
import shutil
import re

from vigilo.common.conf import settings

import vigilo.vigiconf.conf as conf
from vigilo.vigiconf.lib.generators import GeneratorManager
from vigilo.vigiconf.lib.confclasses.host import Host
from vigilo.vigiconf.applications.nagios import Nagios
from vigilo.vigiconf.applications.vigimap import VigiMap
from vigilo.vigiconf.applications.connector_metro import ConnectorMetro

from vigilo.models.tables import ConfFile
from vigilo.models.demo.functions import add_host
from vigilo.models.session import DBSession

from helpers import setup_tmpdir, DummyRevMan
from helpers import setup_db, teardown_db

from vigilo.vigiconf.applications.nagios.generator import NagiosGen


class Generator(unittest.TestCase):

    def setUp(self):
        setup_db()

        # Prepare temporary directory
        self.tmpdir = setup_tmpdir()
        self.basedir = os.path.join(self.tmpdir, "deploy")
        self.old_conf_path = settings["vigiconf"]["confdir"]
        settings["vigiconf"]["confdir"] = os.path.join(self.tmpdir, "conf.d")
        os.mkdir(settings["vigiconf"]["confdir"])
        #conf.hosttemplatefactory.load_templates()
        #reload_conf()
        #conf.load_general_conf()
        #conf.load_xml_conf()
        #self.dispatchator = dispatchmodes.getinstance()
        #self.dispatchator.force = True
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
        """Call after every test case."""
        DBSession.expunge_all()
        teardown_db()
        conf.hostfactory.hosts = {}
        conf.hostsConf = conf.hostfactory.hosts
        shutil.rmtree(self.tmpdir)
        settings["vigiconf"]["confdir"] = self.old_conf_path

    def test_generation(self):
        """Globally test the generation"""
        # Fill with random definitions...
        test_list = conf.testfactory.get_test("Interface", self.host.classes)
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
        test_list = conf.testfactory.get_test("Interface", self.host.classes)
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
                use\s+generic-passive-service\s*
                host_name\s+testserver1\s*          # Working on the testserver1 host
                service_description\s+Traffic[ ]in[ ]eth1\s*
                [^\}]+                              # Any following declaration
                \}                                  # End of the host definition
            """,
            re.MULTILINE | re.VERBOSE)
        self.assert_(regexp_coll.search(nagios) is not None,
            "add_metro_service does not generate proper nagios conf "
            "(Collector service)")
        self.assert_(regexp_svc.search(nagios) is not None,
            "add_metro_service does not generate proper nagios conf "
            "(passive service)")


class NagiosGeneratorForTest(NagiosGen):
    def templateAppend(self, filename, template, args):
        """ redefinition pour tester les directives generiques nagios.
        """
        if args.has_key('generic_directives'):
            self.test_host_data = args
        elif args.has_key('generic_sdirectives'):
            if args['generic_sdirectives'] != "":
                self.test_srv_data = args
        super(NagiosGeneratorForTest, self).templateAppend(filename,
                template, args)


class TestGenericDirNagiosGeneration(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        # Prepare temporary directory
        self.tmpdir = setup_tmpdir()
        self.basedir = os.path.join(self.tmpdir, "deploy")
        # on charge en conf un host avec directives generiques nagios
        setup_db()
        self.host = Host(conf.hostsConf, "dummy.xml", "testserver1",
                         "192.168.1.1", "Servers")
        conffile = ConfFile.get_or_create("dummy.xml")
        add_host("testserver1", conffile)
        self.apps = {"nagios": Nagios(), "vigimap": VigiMap(),
                     "connector-metro": ConnectorMetro()}
        self.ventilation = {"testserver1": {}}
        for appname in self.apps:
            self.ventilation["testserver1"][appname] = "sup.example.com"

    def tearDown(self):
        """Call after every test case."""
        DBSession.expunge_all()
        teardown_db()
        shutil.rmtree(self.tmpdir)

    def test_nagios_directives(self):

        self.host.add_nagios_directive("max_check_attempts", "5")
        self.host.add_nagios_directive("check_interval", "10")
        self.host.add_nagios_directive("retry_interval", "1")

        #ventilator = get_ventilator(apps.values())
        #mapping = ventilator.ventilate()
        #vba = ventilator.ventilation_by_appname(mapping)
        #tpl = NagiosGeneratorForTest(apps["nagios"], ventilation)
        #tpl.generate()
        # recuperation de la generation pour host
        #nagdirs = tpl.test_host_data['generic_directives']
        #print nagdirs

        self.apps["nagios"].generate(self.ventilation)
        nagiosconffile = os.path.join(self.basedir, "sup.example.com",
                                      "nagios", "nagios.cfg")
        self.assert_(os.path.exists(nagiosconffile),
                     "Nagios conf file was not generated")
        nagiosconf = open(nagiosconffile).read()
        print nagiosconf

        self.assertTrue(nagiosconf.find("max_check_attempts    5") >= 0,
            "nagios generator generates max_check_attempts=5")

        self.assertTrue(nagiosconf.find("check_interval    10") >= 0,
            "nagios generator generates check_interval=10")

        self.assertTrue(nagiosconf.find("retry_interval    1") >= 0,
            "nagios generator generates retry_interval=1")

    def test_nagios_service_directives(self):
        #pp = pprint.PrettyPrinter(indent=4)
        #pp.pprint(tpl.test_host_data)
        # recuperation de la generation pour services
        #nagdirs = tpl.test_srv_data['generic_sdirectives']
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

        self.assertTrue(nagiosconf.find("max_check_attempts    6") >= 0,
            "nagios generator generates max_check_attempts=6")

        self.assertTrue(nagiosconf.find("check_interval    11") >= 0,
            "nagios generator generates check_interval=11")

        self.assertTrue(nagiosconf.find("retry_interval    2") >= 0,
            "nagios generator generates retry_interval=2")


# vim:set expandtab tabstop=4 shiftwidth=4:
