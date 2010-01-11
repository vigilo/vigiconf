#!/usr/bin/env python
"""
Test that the generation works properly
"""

import sys, os, unittest, tempfile, shutil, glob, re

import vigilo.vigiconf.conf as conf
import vigilo.vigiconf.generator as generator
from vigilo.vigiconf.lib.confclasses.host import Host

from confutil import reload_conf, setup_tmpdir


class Generator(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        # Prepare temporary directory
        self.tmpdir = setup_tmpdir()
        self.basedir = os.path.join(self.tmpdir, "deploy")
        conf.hosttemplatefactory.load_templates()
        reload_conf()
        self.host = Host(conf.hostsConf, "testserver1", "192.168.1.1", "Servers")
        self.mapping = generator.getventilation()

    def tearDown(self):
        """Call after every test case."""
        shutil.rmtree(self.tmpdir)

    def get_supserver(self, host, app):
        """Return the supervision server from the ventilation"""
        return self.mapping[host.name][app]

    def test_generation(self):
        """Globally test the generation"""
        # Fill with random definitions...
        test_list = conf.testfactory.get_test("Interface", self.host.classes)
        self.host.add_tests(test_list, label="eth1", ifname="eth1")
        self.host.add_metro_service("Traffic in eth1", "ineth1", 10, 20)
        self.host.add_collector_metro("TestAddCS", "TestAddCSMFunction",
                            ["fake arg 1"], ["GET/.1.3.6.1.2.1.1.3.0"],
                            "GAUGE", label="TestAddCSLabel")
        host2 = Host(conf.hostsConf, "testserver2", "192.168.1.2", "Servers")
        host2.add_collector_service( "TestAddCSReRoute", "TestAddCSReRouteFunction",
                ["fake arg 1"], ["GET/.1.3.6.1.2.1.1.3.0"],
                reroutefor={'host': "testserver1", "service": "TestAddCSReRoute"} )
        # Try the generation
        generator.generate(self.basedir)

    def test_add_metro_service_nagios(self):
        """Test for the add_metro_service method"""
        test_list = conf.testfactory.get_test("Interface", self.host.classes)
        self.host.add_tests(test_list, label="eth1", ifname="eth1")
        self.host.add_metro_service("Traffic in eth1", "ineth1", 10, 20)
        generator.generate(self.basedir)
        nagiosconf = os.path.join(self.basedir,
                                  self.get_supserver(self.host, "nagios"),
                                  "nagios.cfg")
        assert os.path.exists(nagiosconf), \
            "Nagios conf file was not generated"
        nagios = open(nagiosconf).read()
        regexp = re.compile(r"""
            define\s+service\s*\{       # Inside an service definition
                [^\}]+                  # Any previous declaration
                host_name\s+testserver1 # Working on the testserver1 host
                [^\}]+                  # Any following declaration
                check_command\s+check_nrpe_rerouted!%s!check_rrd!testserver1/aW5ldGgx\s10\s20\s1
                [^\}]+                  # Any following declaration
                \}                      # End of the host definition
            """ % self.get_supserver(self.host, "storeme").replace(".", "\\."),
            re.MULTILINE | re.VERBOSE)
        assert regexp.search(nagios) is not None, \
            "add_metro_service does not generate proper nagios conf"

    def test_add_tag_host(self):
        """Test for the add_tag host method on hosts"""
        self.host.add_tag("Host", "important", 2)
        generator.generate(self.basedir)
        sqlconf = os.path.join(self.basedir,
                               self.get_supserver(self.host, "dashboard_db"),
                               "dashboard_db", "dashboard_db.sql")
        assert os.path.exists(sqlconf), \
            "Dashboard conf file was not generated"
        sql = open(sqlconf).read()
        assert sql.count("INSERT INTO `tags` (`host`, `service`, `tag`, `value`) VALUES "
                        +"('testserver1', '', 'important', '2');""") > 0, \
                        "add_tag on hosts does not generate proper SQL"

    def test_add_tag_service(self):
        """Test for the add_tag host method on services"""
        test_list = conf.testfactory.get_test("UpTime", self.host.classes)
        self.host.add_tests(test_list)
        self.host.add_tag("UpTime", "security", 1)
        generator.generate(self.basedir)
        sqlconf = os.path.join(self.basedir,
                               self.get_supserver(self.host, "dashboard_db"),
                               "dashboard_db", "dashboard_db.sql")
        assert os.path.exists(sqlconf), \
            "Dashboard conf file was not generated"
        sql = open(sqlconf).read()
        assert sql.count("INSERT INTO `tags` (`host`, `service`, `tag`, `value`) VALUES "
                        +"('testserver1', 'UpTime', 'security', '1');""") > 0, \
                        "add_tag on services does not generate proper SQL"



# vim:set expandtab tabstop=4 shiftwidth=4:
