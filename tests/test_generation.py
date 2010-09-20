#!/usr/bin/env python
"""
Test that the generation works properly
"""

import sys, os, unittest, tempfile, shutil, glob, re

import vigilo.vigiconf.conf as conf
from vigilo.vigiconf.lib import dispatchmodes
from vigilo.vigiconf.lib.generators import GeneratorManager
from vigilo.vigiconf.lib.validator import Validator
from vigilo.vigiconf.lib.loaders import LoaderManager
from vigilo.vigiconf.lib.confclasses.host import Host
from vigilo.models.tables import MapGroup
from vigilo.models.demo.functions import add_host

from confutil import reload_conf, setup_tmpdir
from confutil import setup_db, teardown_db

from vigilo.vigiconf.applications.nagios.generator import NagiosGen

import pprint

class Generator(unittest.TestCase):
    def setUp(self):
        """Call before every test case."""
        setup_db()
        MapGroup(name=u'Root')

        # Prepare temporary directory
        self.tmpdir = setup_tmpdir()
        self.basedir = os.path.join(self.tmpdir, "deploy")
        conf.hosttemplatefactory.load_templates()
        reload_conf()
        self.dispatchator = dispatchmodes.getinstance()
        self.host = Host(conf.hostsConf, "testserver1", "192.168.1.1", "Servers")
        add_host("testserver1")
        add_host("localhost")
        add_host("localhost2")
        loader = LoaderManager()
        loader.load_apps_db(self.dispatchator.applications)
        loader.load_vigilo_servers_db()
        self.genmanager = GeneratorManager(self.dispatchator.applications)
        self.mapping = self.genmanager.get_ventilation()

    def tearDown(self):
        """Call after every test case."""
        teardown_db()
        shutil.rmtree(self.tmpdir)

    def get_supserver(self, host, app):
        """Return the supervision server from the ventilation"""
        for mapped_app in self.mapping[host.name]:
            if mapped_app.name == app:
                return self.mapping[host.name][mapped_app]

    def test_generation(self):
        """Globally test the generation"""
        # Fill with random definitions...
        test_list = conf.testfactory.get_test("Interface", self.host.classes)
        self.host.add_tests(test_list, {"label":"eth1", "ifname":"eth1"})
        self.host.add_metro_service("Traffic in eth1", "ineth1", 10, 20)
        self.host.add_collector_metro("TestAddCS", "TestAddCSMFunction",
                            ["fake arg 1"], ["GET/.1.3.6.1.2.1.1.3.0"],
                            "GAUGE", label="TestAddCSLabel")
        host2 = Host(conf.hostsConf, "testserver2", "192.168.1.2", "Servers")
        host2.add_collector_service( "TestAddCSReRoute", "TestAddCSReRouteFunction",
                ["fake arg 1"], ["GET/.1.3.6.1.2.1.1.3.0"],
                reroutefor={'host': "testserver1", "service": "TestAddCSReRoute"} )
        # Try the generation
        self.genmanager.generate()

    def test_add_metro_service_nagios(self):
        """Test for the add_metro_service method"""
        test_list = conf.testfactory.get_test("Interface", self.host.classes)
        self.host.add_tests(test_list, {"label":"eth1", "ifname":"eth1"})
        self.host.add_metro_service("Traffic in eth1", "ineth1", 10, 20)
        self.genmanager.generate()
        nagiosconf = os.path.join(self.basedir,
                                  self.get_supserver(self.host, "nagios"),
                                  "nagios", "nagios.cfg")
        assert os.path.exists(nagiosconf), \
            "Nagios conf file was not generated"
        nagios = open(nagiosconf).read()

        regexp = re.compile(r"""
            define\s+service\s*\{       # Inside an service definition
                [^\}]+                  # Any previous declaration
                host_name\s+testserver1 # Working on the testserver1 host
                [^\}]+                  # Any following declaration
                check_command\s+check_nrpe_rerouted!localhost2?!check_rrd!testserver1/ineth1\s10\s20\s1
                [^\}]+                  # Any following declaration
                \}                      # End of the host definition
            """,
            re.MULTILINE | re.VERBOSE)
        assert regexp.search(nagios) is not None, \
            "add_metro_service does not generate proper nagios conf"


class NagiosGeneratorForTest(NagiosGen):
    def templateAppend(self, filename, template, args):
        """ redefinition pour tester les directives generiques nagios.
        """
        if args.has_key('generic_directives'):
            self.test_host_data = args
        elif args.has_key('generic_sdirectives'):
            if args['generic_sdirectives'] != "":
                self.test_srv_data = args
        super(NagiosGeneratorForTest, self).templateAppend(filename, template, args)


class TestGenericDirNagiosGeneration(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        # Prepare temporary directory
        self.tmpdir = setup_tmpdir()
        self.basedir = os.path.join(self.tmpdir, "deploy")
        conf.hosttemplatefactory.load_templates()
        # on charge en conf un host avec directives generiques nagios
        setup_db()
        reload_conf(hostsdir='tests/testdata/generators/nagios/')
        self.dispatchator = dispatchmodes.getinstance()
        self.nagios_app = [ a for a in self.dispatchator.applications if a.name == "nagios" ][0]
        add_host("example-nagios-spec.xml")
        loader = LoaderManager()
        loader.load_apps_db(self.dispatchator.applications)
        loader.load_vigilo_servers_db()
        self.genmanager = GeneratorManager(self.dispatchator.applications)
        self.mapping = self.genmanager.get_ventilation()

    def tearDown(self):
        """Call after every test case."""
        teardown_db()
        shutil.rmtree(self.tmpdir)

    def test_nagios_generator(self):
        v = Validator(self.mapping)
        vba = self.genmanager.ventilation_by_appname(self.mapping)
        tpl = NagiosGeneratorForTest(self.nagios_app, vba, v)
        tpl.generate()
        # recuperation de la generation pour host
        nagdirs = tpl.test_host_data['generic_directives']
        print nagdirs

        self.assertTrue(nagdirs.find("max_check_attempts    5") >= 0,
            "nagios generator generates max_check_attempts=5")

        self.assertTrue(nagdirs.find("check_interval    10") >= 0,
            "nagios generator generates check_interval=10")

        self.assertTrue(nagdirs.find("retry_interval    1") >= 0,
            "nagios generator generates retry_interval=1")

        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(tpl.test_host_data)
        # recuperation de la generation pour services
        nagdirs = tpl.test_srv_data['generic_sdirectives']

        self.assertTrue(nagdirs.find("max_check_attempts    6") >= 0,
            "nagios generator generates max_check_attempts=6")

        self.assertTrue(nagdirs.find("check_interval    11") >= 0,
            "nagios generator generates check_interval=11")

        self.assertTrue(nagdirs.find("retry_interval    2") >= 0,
            "nagios generator generates retry_interval=2")


# vim:set expandtab tabstop=4 shiftwidth=4:
