#!/usr/bin/env python
import sys, os, unittest, tempfile, shutil, glob

import vigilo.vigiconf.conf as conf
from vigilo.vigiconf.lib.confclasses.host import Host

from confutil import reload_conf

class HostMethods(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        reload_conf()
        self.host = Host(conf.hostsConf, u"testserver1", u"192.168.1.1", u"Servers")

    def tearDown(self):
        """Call after every test case."""
        pass


    def test_add_metro_service(self):
        """Test for the add_metro_service host method"""
        test_list = conf.testfactory.get_test("Interface", self.host.classes)
        self.host.add_tests(test_list, label="eth1", ifname="eth1")
        self.host.add_metro_service("Traffic in eth1", "ineth1", 10, 20)
        assert conf.hostsConf["testserver1"]["services"]["Traffic in eth1"]["command"] == \
                "check_nrpe_rerouted!$METROSERVER$!check_rrd!testserver1/aW5ldGgx 10 20 1", \
                "add_metro_service does not work"

    def test_priority_host_hosttemplate(self):
        """Test priorité du paramétrage des host sur les hosttemplates"""
        assert conf.hostsConf["localhost"]["services"]["Traffic in eth0"]["command"] == \
                "check_nrpe_rerouted!$METROSERVER$!check_rrd!localhost/aW5ldGgw 15 35 8"

    def test_add_metro_service_INTF(self):
        """Test for the add_metro_service function in the Interface test"""
        test_list = conf.testfactory.get_test("Interface", self.host.classes)
        self.host.add_tests(test_list, label="eth0", ifname="eth0", warn="10,20", crit="30,40")
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
        test_list = conf.testfactory.get_test("UpTime", self.host.classes)
        self.host.add_tests(test_list)
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
        host2 = Host(conf.hostsConf, "testserver2", "192.168.1.2", "Servers")
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
        host2 = Host(conf.hostsConf, u"testserver2", u"192.168.1.2", "Servers")
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
    
    def test_add_nagios_directive(self):
        """ Test for the add_nagios_directive method
        """
        host = Host(conf.hostsConf, u"testserver2", u"192.168.1.2", "Servers")
        host.add_nagios_directive("max_check_attempts", "5")
        self.assertEquals(conf.hostsConf["testserver2"]["nagiosDirectives"]["max_check_attempts"],
                          "5")
                

    
    def test_add_nagios_service_directive(self):
        """ Test for the add_nagios_service_directive method
        """
        host = Host(conf.hostsConf, u"testserver2", u"192.168.1.2", "Servers")
        host.add_nagios_service_directive("Interface", "retry_interval", "10")
        self.assertEquals(
            conf.hostsConf["testserver2"]["nagiosSrvDirs"]["Interface"]["retry_interval"],
            "10")
 

from vigilo.vigiconf.lib.confclasses.host import HostFactory
from vigilo.common.conf import settings

class HostFactoryMethods(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        reload_conf()

    def tearDown(self):
        """Call after every test case."""
        pass
    
    def test_load(self):
        """ Test of the loading of the conf test hosts
        """
        f = HostFactory(
                os.path.join(settings["vigiconf"].get("confdir"), "hosts"),
                conf.hosttemplatefactory,
                conf.testfactory,
            )
        hosts = f.load()
        self.assertTrue(hosts.has_key('localhost'), "localhost defined in conf")
        
    
    def test_load_with_nagios_directives(self):
        """ Test of the loading of host with nagios directives
        """
        f = HostFactory(
                "tests/testdata/xsd/hosts/ok",
                conf.hosttemplatefactory,
                conf.testfactory,
            )
        # validation par XSD
        hosts = f.load(validation=True)
        testserver1 = hosts['testserver1']
        nagiosdirs = testserver1.get('nagiosDirectives')
        self.assertEquals(nagiosdirs['max_check_attempts'], "5",
                          "max_check_attempts=5")
        self.assertEquals(nagiosdirs['check_interval'], "10",
                          "check_interval=10")
        self.assertEquals(nagiosdirs['retry_interval'], "1",
                          "retry_interval=1")
        
        nagios_sdirs = testserver1.get('nagiosSrvDirs')
        self.assertEquals(nagios_sdirs['Interface eth0']['max_check_attempts'], "5",
                          "max_check_attempts=5")
        self.assertEquals(nagios_sdirs['Interface eth0']['check_interval'], "10",
                          "check_interval=10")
        self.assertEquals(nagios_sdirs['Interface eth0']['retry_interval'], "1",
                          "retry_interval=1")


# vim:set expandtab tabstop=4 shiftwidth=4:
