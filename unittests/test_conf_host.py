#!/usr/bin/env python
import sys, os, unittest, tempfile, shutil, glob
from pprint import pprint

import conf
from lib.confclasses.host import Host


class HostMethods(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        conf.confDir = "../src/conf.d"
        conf.dataDir = "../src"
        # We changed the paths, reload the factories
        conf.hosttemplatefactory.__init__()
        conf.testfactory.__init__()
        # Load the configuration
        conf.loadConf()
        self.host = Host("testserver1", "192.168.1.1", "Servers")

    def tearDown(self):
        """Call after every test case."""
        pass


    def test_add_metro_service(self):
        """Test for the add_metro_service host method"""
        self.host.add_test("Interface", label="eth1", ifname="eth1")
        self.host.add_metro_service("Traffic in eth1", "ineth1", 10, 20)
        assert conf.hostsConf["testserver1"]["services"]["Traffic in eth1"]["command"] == \
                "check_nrpe_rerouted!$METROSERVER$!check_rrd!testserver1/aW5ldGgx 10 20 1", \
                "add_metro_service does not work"

    def test_add_metro_service_INTF(self):
        """Test for the add_metro_service function in the Interface test"""
        self.host.add_test( "Interface", label="eth0", ifname="eth0", warn="10,20", crit="30,40" )
        assert conf.hostsConf["testserver1"]["services"]["Traffic in eth0"]["command"] == \
                "check_nrpe_rerouted!$METROSERVER$!check_rrd!testserver1/aW5ldGgw 10 30 8", \
                "add_metro_service does not work in Interface (in) test"
        assert conf.hostsConf["testserver1"]["services"]["Traffic out eth0"]["command"] == \
                "check_nrpe_rerouted!$METROSERVER$!check_rrd!testserver1/b3V0ZXRoMA== 20 40 8", \
                "add_metro_service does not work in Interface (out) test"

    def test_add_tag_hosts(self):
        """Test for the add_tag host method"""
        self.host.add_tag("Host", "important", 2)
        assert conf.hostsConf["testserver1"]["tags"] == {"important": 2}, \
                "add_tag does not work on hosts"

    def test_add_tag_services(self):
        """Test for the add_tag host method"""
        self.host.add_test("UpTime")
        self.host.add_tag("UpTime", "security", 1)
        assert conf.hostsConf["testserver1"]["services"]["UpTime"]["tags"] == {"security": 1}, \
                "add_tag does not work on services"

    def test_add_trap(self):
        """Test for the add_trap host method"""
        self.host.add_trap("test.add_trap", "test.name", "test.label.wrong")
        self.host.add_trap("test.add_trap", "test.name", "test.label")
        assert conf.hostsConf["testserver1"]["trapItems"]["test.add_trap"]["test.name"] == "test.label", \
                "add_trap does not work"

    def test_add_group(self):
        """Test for the add_group host method"""
        self.host.add_group("Test Group")
        assert conf.hostsConf["testserver1"]["otherGroups"].has_key("Test Group"), \
                "add_group does not work"
        assert "Test Group" in conf.groupsHierarchy["Servers"], \
                "add_group does not update the groupHierarchy"

    def test_add_collector_service(self):
        """Test for the add_collector_service host method"""
        self.host.add_collector_service( "TestAddCS", "TestAddCSFunction",
                                ["fake arg 1"], ["GET/.1.3.6.1.2.1.1.3.0"] )
        assert conf.hostsConf["testserver1"]["services"]["TestAddCS"]["type"] == "passive", \
                "add_collector_service does not fill the services sub-hashmap"
        assert conf.hostsConf["testserver1"]["SNMPJobs"][("TestAddCS","service")] == \
                {'function': "TestAddCSFunction", 'params': ["fake arg 1"], \
                 'vars': ["GET/.1.3.6.1.2.1.1.3.0"], 'reRouteFor': None}, \
                "add_collector_service does not fill the SNMPJobs sub-hashmap"

    def test_add_collector_service_reroute(self):
        """Test for the add_collector_service host method with rerouting"""
        host2 = Host("testserver2", "192.168.1.2", "Servers")
        host2.add_collector_service( "TestAddCSReRoute", "TestAddCSReRouteFunction",
                ["fake arg 1"], ["GET/.1.3.6.1.2.1.1.3.0"],
                reroutefor={'host': "testserver1", "service": "TestAddCSReRoute"} )
        assert conf.hostsConf["testserver1"]["services"]["TestAddCSReRoute"]["type"] == "passive", \
                "add_collector_service rerouting does not work with the services sub-hashmap"
        assert conf.hostsConf["testserver2"]["SNMPJobs"][("TestAddCSReRoute","service")] == \
                {'function': "TestAddCSReRouteFunction", 'params': ["fake arg 1"], \
                 'vars': ["GET/.1.3.6.1.2.1.1.3.0"], 'reRouteFor': \
                 {'host':"testserver1", "service" : "TestAddCSReRoute"}}, \
                "add_collector_service rerouting does not work with the SNMPJobs sub-hashmap"

    def test_add_collector_metro(self):
        """Test for the add_collector_metro host method"""
        self.host.add_collector_metro("TestAddCS", "TestAddCSMFunction",
                            ["fake arg 1"], ["GET/.1.3.6.1.2.1.1.3.0"],
                            "GAUGE", label="TestAddCSLabel")
        assert conf.hostsConf["testserver1"]["dataSources"]["TestAddCS"] == \
                {'dsType':"GAUGE", 'label': "TestAddCSLabel"}, \
                "add_collector_metro does not fill the dataSources sub-hashmap"
        assert conf.hostsConf["testserver1"]["SNMPJobs"][("TestAddCS","perfData")] == \
                {'function': "TestAddCSMFunction", 'params': ["fake arg 1"], \
                 'vars': ["GET/.1.3.6.1.2.1.1.3.0"], 'reRouteFor': None}, \
                "add_collector_metro does not fill the SNMPJobs sub-hashmap"

    def test_add_collector_metro_reroute(self):
        """Test for the add_collector_metro host method with rerouting"""
        host2 = Host("testserver2", "192.168.1.2", "Servers")
        host2.add_collector_metro( "TestAddCSReRoute", "TestAddCSRRMFunction",
                ["fake arg 1"], ["GET/.1.3.6.1.2.1.1.3.0"],
                "GAUGE", label="TestAddCSReRouteLabel",
                reroutefor={'host': "testserver1", "service": "TestAddCSReRoute"} )
        assert conf.hostsConf["testserver1"]["dataSources"]["TestAddCSReRoute"] == \
                {'dsType':"GAUGE", 'label': "TestAddCSReRouteLabel"}, \
                "add_collector_metro rerouting does not work with the dataSources sub-hashmap"
        assert conf.hostsConf["testserver2"]["SNMPJobs"][("TestAddCSReRoute","perfData")] == \
                {'function': "TestAddCSRRMFunction", 'params': ["fake arg 1"], \
                 'vars': ["GET/.1.3.6.1.2.1.1.3.0"], 'reRouteFor': \
                 {'host':"testserver1", "service" : "TestAddCSReRoute"}}, \
                "add_collector_service ReRouting does not work with the SNMPJobs sub-hashmap"



# vim:set expandtab tabstop=4 shiftwidth=4:
