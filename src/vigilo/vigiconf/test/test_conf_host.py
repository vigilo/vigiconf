#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os, unittest, tempfile, shutil, glob

import vigilo.vigiconf.conf as conf
from vigilo.vigiconf.lib.confclasses.host import Host
from vigilo.vigiconf.lib.confclasses.hosttemplate import HostTemplate

from helpers import setup_db, teardown_db, setup_tmpdir, TESTDATADIR

class HostMethods(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        setup_db()
        self.host = Host(conf.hostsConf, "dummy", u"testserver1", u"192.168.1.1", u"Servers")

    def tearDown(self):
        """Call after every test case."""
        conf.hostfactory.hosts = {}
        conf.hostsConf = conf.hostfactory.hosts
        teardown_db()

    def test_add_metro_service(self):
        """Test for the add_metro_service host method"""
        test_list = conf.testfactory.get_test("Interface", self.host.classes)
        self.host.add_tests(test_list, {"label":"eth1", "ifname":"eth1"})
        self.host.add_metro_service("Traffic in eth1", "ineth1", 10, 20)
        self.assertEqual(
            conf.hostsConf["testserver1"]["services"]["Traffic in eth1"]
                ["type"], "passive")
        self.assert_( ('Traffic in eth1', 'service') in
                      conf.hostsConf["testserver1"]["metro_services"] )

    def test_priority_host_hosttemplate(self):
        """Test priorite du parametrage des hosts sur les hosttemplates"""
        test_list = conf.testfactory.get_test("Interface", self.host.classes)
        self.host.add_tests(test_list, {"label":"eth0", "ifname":"eth0"})
        self.host.add_metro_service("Traffic in eth0", "ineth0", 10, 20)
        self.assertEqual(
            conf.hostsConf["testserver1"]["services"]["Traffic in eth0"]
                ["type"], "passive")

    def test_add_metro_service_INTF(self):
        """Test for the add_metro_service function in the Interface test"""
        test_list = conf.testfactory.get_test("Interface", self.host.classes)
        self.host.add_tests(test_list, {"label":"eth0", "ifname":"eth0", "warn":"10,20", "crit":"30,40"})
        self.assertEqual(
            conf.hostsConf["testserver1"]["services"]["Traffic in eth0"]
                ["type"], "passive")
        self.assert_( ('Traffic in eth0', 'service') in
                      conf.hostsConf["testserver1"]["metro_services"] )

        self.assertEqual(
            conf.hostsConf["testserver1"]["services"]["Traffic out eth0"]
                ["type"], "passive")
        self.assert_( ('Traffic out eth0', 'service') in
                      conf.hostsConf["testserver1"]["metro_services"] )

    def test_add_tag_hosts(self):
        """Test for the add_tag method on hosts"""
        self.host.add_tag("Host", "important", 2)
        self.assertEqual(conf.hostsConf["testserver1"]["tags"], {"important": 2})

    def test_add_tag_services(self):
        """Test for the add_tag method on services"""
        test_list = conf.testfactory.get_test("UpTime", self.host.classes)
        self.host.add_tests(test_list)
        self.host.add_tag("UpTime", "security", 1)
        self.assertEqual(conf.hostsConf["testserver1"]["services"]["UpTime"]["tags"], {"security": 1})

    def test_add_trap(self):
        """Test for the add_trap method on hosts"""
        data = {}
        data["command"] = "test_path_to_script"
        data["service"] = "test_serv"
        data["label"] = "test.label"
        self.host.add_trap("test_serv", "1.2.3.4.5.6.7.8.9", data)
        self.assertEqual(
                conf.hostsConf["testserver1"]["snmpTrap"]["test_serv"]["1.2.3.4.5.6.7.8.9"]["label"],
                "test.label")

    def test_add_group(self):
        """Test for the add_group method on hosts"""
        self.host.add_group("/Test Group")
        assert "/Test Group" in conf.hostsConf["testserver1"]["otherGroups"], \
                "add_group does not work"

    def test_add_collector_service(self):
        """Test for the add_collector_service method on hosts"""
        self.host.add_collector_service(
            "TestAddCS",
            "TestAddCSFunction",
            ["fake arg 1"],
            ["GET/.1.3.6.1.2.1.1.3.0"]
        )
        assert conf.hostsConf["testserver1"]["services"] \
            ["TestAddCS"]["type"] == "passive", \
            "add_collector_service does not fill the services sub-hashmap"
        assert conf.hostsConf["testserver1"]["SNMPJobs"] \
            [("TestAddCS", "service")] == {
                'function': "TestAddCSFunction",
                'params': ["fake arg 1"],
                'vars': ["GET/.1.3.6.1.2.1.1.3.0"],
                'reRouteFor': None,
            }, "add_collector_service does not fill the SNMPJobs sub-hashmap"

    def test_add_collector_service_reroute(self):
        """Test for the add_collector_service host method with rerouting"""
        host2 = Host(conf.hostsConf, "dummy", "testserver2", "192.168.1.2", "Servers")
        host2.add_collector_service(
            "TestAddCSReRoute",
            "TestAddCSReRouteFunction",
            ["fake arg 1"],
            ["GET/.1.3.6.1.2.1.1.3.0"],
            reroutefor={
                'host': "testserver1",
                "service": "TestAddCSReRoute",
            },
        )
        assert conf.hostsConf["testserver1"]["services"] \
            ["TestAddCSReRoute"]["type"] == "passive", \
            "add_collector_service rerouting does not work " \
            "with the services sub-hashmap"
        assert conf.hostsConf["testserver2"]["SNMPJobs"] \
            [("TestAddCSReRoute", "service")] == {
                'function': "TestAddCSReRouteFunction",
                'params': ["fake arg 1"],
                 'vars': ["GET/.1.3.6.1.2.1.1.3.0"],
                 'reRouteFor': {
                    'host': "testserver1",
                    "service": "TestAddCSReRoute"
                },
            }, \
            "add_collector_service rerouting does not work " \
                "with the SNMPJobs sub-hashmap"

    def test_add_collector_metro(self):
        """Test for the add_collector_metro host method"""
        self.host.add_collector_metro("TestAddCS", "TestAddCSMFunction",
                            ["fake arg 1"], ["GET/.1.3.6.1.2.1.1.3.0"],
                            "GAUGE", label="TestAddCSLabel")
        self.assertEqual(
            conf.hostsConf["testserver1"]["dataSources"]["TestAddCS"],
            {'dsType':"GAUGE", 'label': "TestAddCSLabel", "max": None, "min": None},
            "add_collector_metro does not fill the dataSources sub-hashmap")
        self.assertEqual(
            conf.hostsConf["testserver1"]["SNMPJobs"][("TestAddCS","perfData")],
            {'function': "TestAddCSMFunction", 'params': ["fake arg 1"],
             'vars': ["GET/.1.3.6.1.2.1.1.3.0"], 'reRouteFor': None},
            "add_collector_metro does not fill the SNMPJobs sub-hashmap")

    def test_add_collector_metro_reroute(self):
        """Test for the add_collector_metro host method with rerouting"""
        host2 = Host(conf.hostsConf, "dummy", u"testserver2", u"192.168.1.2", "Servers")
        host2.add_collector_metro( "TestAddCSReRoute", "TestAddCSRRMFunction",
                ["fake arg 1"], ["GET/.1.3.6.1.2.1.1.3.0"],
                "GAUGE", label="TestAddCSReRouteLabel",
                reroutefor={'host': "testserver1", "service": "TestAddCSReRoute"} )
        self.assertEqual(
            conf.hostsConf["testserver1"]["dataSources"]["TestAddCSReRoute"],
            {'dsType':"GAUGE", 'label': "TestAddCSReRouteLabel", "max": None, "min": None},
            "add_collector_metro rerouting does not work with the dataSources sub-hashmap")
        self.assertEqual(
            conf.hostsConf["testserver2"]["SNMPJobs"][("TestAddCSReRoute","perfData")],
            {'function': "TestAddCSRRMFunction", 'params': ["fake arg 1"],
             'vars': ["GET/.1.3.6.1.2.1.1.3.0"], 'reRouteFor':
             {'host':"testserver1", "service" : "TestAddCSReRoute"}},
            "add_collector_service ReRouting does not work with the SNMPJobs sub-hashmap")

    def test_add_nagios_directive(self):
        """ Test for the add_nagios_directive method
        """
        host = Host(conf.hostsConf, "dummy", u"testserver2", u"192.168.1.2", "Servers")
        host.add_nagios_directive("max_check_attempts", "5")
        self.assertEquals(
            conf.hostsConf["testserver2"]["nagiosDirectives"]["max_check_attempts"],
            "5")

    def test_add_nagios_service_directive(self):
        """ Test for the add_nagios_service_directive method
        """
        host = Host(conf.hostsConf, "dummy", u"testserver2", u"192.168.1.2", "Servers")
        host.add_nagios_service_directive("Interface", "retry_interval", "10")
        self.assertEquals(
            conf.hostsConf["testserver2"]["nagiosSrvDirs"]["Interface"]["retry_interval"],
            "10")


from vigilo.vigiconf.lib.confclasses.host import HostFactory
from vigilo.common.conf import settings

class HostFactoryMethods(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        setup_db()
        self.tmpdir = setup_tmpdir()

    def tearDown(self):
        """Call after every test case."""
        conf.hostfactory.hosts = {}
        conf.hostsConf = conf.hostfactory.hosts
        teardown_db()
        shutil.rmtree(self.tmpdir)


    def test_load(self):
        """ Test of the loading of the conf test hosts
        """
        xmlfile = open(os.path.join(self.tmpdir, "localhost.xml"), "w")
        xmlfile.write("""
            <host name="localhost" address="127.0.0.1">
                <group>Linux servers</group>
            </host>
        """)
        xmlfile.close()
        conf.hosttemplatefactory.register(HostTemplate("default"))
        f = HostFactory(
                self.tmpdir,
                conf.hosttemplatefactory,
                conf.testfactory,
            )
        hosts = f.load()
        print hosts
        self.assertTrue(hosts.has_key('localhost'), "localhost defined in conf")

    def test_load_with_nagios_directives(self):
        """Loading some host with nagios directives."""
        # ces templates sont utilisés dans les fichiers
        for tplname in ["default", "linux"]:
            htpl = HostTemplate(tplname)
            conf.hosttemplatefactory.register(htpl)
        htpl.add_group("dummy_group") # sinon le no_secondary_groups.xml va pas passer
        f = HostFactory(
                os.path.join(TESTDATADIR, "xsd/hosts/ok"),
                conf.hosttemplatefactory,
                conf.testfactory,
            )

        # validation par XSD
        hosts = f.load(validation=True)
        testserver = hosts['example-nagios-spec.xml']
        nagiosdirs = testserver.get('nagiosDirectives')
        print nagiosdirs
        self.assertEquals(nagiosdirs['max_check_attempts'], "5")
        self.assertEquals(nagiosdirs['check_interval'], "10")
        self.assertEquals(nagiosdirs['retry_interval'], "1")

        nagios_sdirs = testserver.get('nagiosSrvDirs')
        print nagios_sdirs
        self.assertEquals(nagios_sdirs['Interface eth0']['max_check_attempts'], "5")
        self.assertEquals(nagios_sdirs['Interface eth0']['check_interval'], "10")
        self.assertEquals(nagios_sdirs['Interface eth0']['retry_interval'], "1")


# vim:set expandtab tabstop=4 shiftwidth=4:
