#!/usr/bin/env python
import sys, os, unittest, tempfile, shutil, glob

import vigilo.vigiconf.conf as conf
from vigilo.vigiconf.lib.confclasses.hosttemplate import HostTemplate
from vigilo.vigiconf.lib.confclasses.host import Host

from helpers import setup_db, teardown_db

class HostTemplates(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        setup_db()
        conf.hosttemplatefactory.register(HostTemplate("default"))
        self.tpl = HostTemplate("testtpl1")
        conf.hosttemplatefactory.register(self.tpl)
        self.host = Host(conf.hostsConf, "dummy", "testserver1", "192.168.1.1", "Servers")

    def tearDown(self):
        """Call after every test case."""
        conf.hostfactory.hosts = {}
        conf.hostsConf = conf.hostfactory.hosts
        conf.hosttemplatefactory.__init__(conf.testfactory)
        teardown_db()


    def test_add_test_simple(self):
        """Test for the add_test method, without test arguments"""
        self.tpl.add_test("UpTime")
        conf.hosttemplatefactory.apply(self.host, "testtpl1")
        assert conf.hostsConf["testserver1"]["services"].has_key("UpTime"), \
                "add_test does not work without test args"

    def test_add_test_args(self):
        """Test for the add_test method, with test arguments"""
        self.tpl.add_test("Interface", {"label":"Loopback", "ifname":"lo"})
        conf.hosttemplatefactory.apply(self.host, "testtpl1")
        assert conf.hostsConf["testserver1"]["SNMPJobs"][('Interface Loopback',
                'service')]["params"] == ["lo", "Loopback", "i"], \
                "add_test does not work with test args"

    def test_add_group_simple(self):
        """Test for the add_group method, with one argument only"""
        self.tpl.add_group("/Test Group")
        conf.hosttemplatefactory.apply(self.host, "testtpl1")
        assert "/Test Group" in conf.hostsConf["testserver1"]["otherGroups"], \
                "add_group does not work with one arg"

    def test_add_group_multiple(self):
        """Test for the add_group method, with multiple arguments"""
        self.tpl.add_group("/Test Group 1", "/Test Group 2")
        conf.hosttemplatefactory.apply(self.host, "testtpl1")
        assert "/Test Group 1" in conf.hostsConf["testserver1"]["otherGroups"], \
                "add_group does not work with multiple args"
        assert "/Test Group 2" in conf.hostsConf["testserver1"]["otherGroups"], \
                "add_group does not work with multiple args"

    def test_add_attribute(self):
        """Test for the add_attribute method"""
        self.tpl.add_attribute("TestAttr", "TestVal")
        conf.hosttemplatefactory.apply(self.host, "testtpl1")
        assert conf.hostsConf["testserver1"]["TestAttr"] == "TestVal", \
                "add_attribute does not work"

    def test_inherit_test(self):
        self.tpl.add_test("UpTime")
        tpl2 = HostTemplate("testtpl2")
        tpl2.add_parent("testtpl1")
        conf.hosttemplatefactory.register(tpl2)
        # Reload the templates
        conf.hosttemplatefactory.load_templates()
        assert "UpTime" in [ t["name"] for t in conf.hosttemplatefactory.templates["testtpl2"]["tests"] ], \
                "inheritance does not work with tests"

    def test_inherit_group(self):
        self.tpl.add_group("Test Group")
        tpl2 = HostTemplate("testtpl2")
        tpl2.add_parent("testtpl1")
        conf.hosttemplatefactory.register(tpl2)
        # Reload the templates
        conf.hosttemplatefactory.load_templates()
        assert "Test Group" in conf.hosttemplatefactory.templates["testtpl2"]["groups"], \
                "inheritance does not work with groups"

    def test_inherit_attribute(self):
        self.tpl.add_attribute("TestAttr", "TestVal")
        tpl2 = HostTemplate("testtpl2")
        tpl2.add_parent("testtpl1")
        conf.hosttemplatefactory.register(tpl2)
        # Reload the templates
        conf.hosttemplatefactory.load_templates()
        assert conf.hosttemplatefactory.templates["testtpl2"]["attributes"].has_key("TestAttr"), \
                "inheritance does not work with attributes"
        assert conf.hosttemplatefactory.templates["testtpl2"]["attributes"]["TestAttr"] == "TestVal", \
                "inheritance does not work with attributes"

    def test_inherit_redefine_test(self):
        self.tpl.add_test("Interface", {"ifname":"eth0", "label":"Label1"})
        tpl2 = HostTemplate("testtpl2")
        tpl2.add_parent("testtpl1")
        tpl2.add_test("Interface", {"ifname":"eth0", "label":"Label2"})
        conf.hosttemplatefactory.register(tpl2)
        # Reload the templates
        conf.hosttemplatefactory.load_templates()
        intftest = None
        for test in conf.hosttemplatefactory.templates["testtpl2"]["tests"]:
            if test["name"] == "Interface":
                intftest = test
        assert intftest is not None, "inheritance does not work with tests"
        assert intftest["args"]["label"] == "Label2", \
                "child templates cannot redefine tests from parent templates"

    def test_inherit_multiple_test(self):
        self.tpl.add_test("Interface", {"ifname":"eth0", "label":"Label0"})
        tpl2 = HostTemplate("testtpl2")
        tpl2.add_test("Interface", {"ifname":"eth1", "label":"Label1"})
        conf.hosttemplatefactory.register(tpl2)
        tpl3 = HostTemplate("testtpl3")
        tpl3.add_parent(["testtpl1", "testtpl2"])
        conf.hosttemplatefactory.register(tpl3)
        # Reload the templates
        conf.hosttemplatefactory.load_templates()
        intftests = []
        for test in conf.hosttemplatefactory.templates["testtpl3"]["tests"]:
            if test["name"] == "Interface":
                intftests.append(test["args"]["ifname"])
        assert intftests == [ "eth0", "eth1"], \
                "multiple inheritance does not work (%s)" % str(intftests)

    def test_deepcopy(self):
        """
        If the template data from the parent is not copied with
        copy.deepcopy(), then the child's template data will propagate back
        into the parent
        """
        self.tpl.add_attribute("TestAttr1", "TestVal")
        tpl2 = HostTemplate("testtpl2")
        tpl2.add_parent("testtpl1")
        tpl2.add_attribute("TestAttr2", "TestVal")
        conf.hosttemplatefactory.register(tpl2)
        # Reload the templates
        conf.hosttemplatefactory.load_templates()
        assert not conf.hosttemplatefactory.templates["testtpl1"]["attributes"].has_key("TestAttr2"), \
                "inheritence taints parent templates"

    def test_defined_templates(self):
        conf.hosttemplatefactory.load_templates()
        for tpl in conf.hosttemplatefactory.templates.keys():
            conf.hosttemplatefactory.apply(self.host, tpl)

    def test_parent_default(self):
        tpl1 = HostTemplate("testtpl2")
        tpl1.add_parent("testtpl1")
        conf.hosttemplatefactory.register(tpl1)
        assert "default" in conf.hosttemplatefactory.templates["testtpl1"]["parent"], \
                "The \"default\" template is not automatically added as parent to other templates"


    def test_add_nagios_directive(self):
        """ Test for the add_nagios_directive method
        """
        self.tpl.add_nagios_directive("max_check_attempts", "5")
        self.assertEquals(conf.hosttemplatefactory.templates["testtpl1"]["nagiosDirectives"]["max_check_attempts"],
                          "5")



    def test_add_nagios_service_directive(self):
        """ Test for the add_nagios_service_directive method
        """
        self.tpl.add_nagios_service_directive("Interface eth1", "retry_interval", "10")
        self.assertEquals(
            conf.hosttemplatefactory.templates["testtpl1"]["nagiosSrvDirs"]["Interface eth1"]["retry_interval"],
            "10")

    def test_nagiosdirs_apply_on_host(self):
        self.tpl.add_nagios_directive("retry_interval", "8")
        conf.hosttemplatefactory.apply(self.host, "testtpl1")
        testserver1 = conf.hostsConf['testserver1']
        nagiosdirs = testserver1.get('nagiosDirectives')
        self.assertEquals(nagiosdirs['retry_interval'], "8",
                          "retry_interval=8")

    def test_nagios_srvdirs_apply_on_host(self):
        self.tpl.add_nagios_service_directive("Interface eth0", "retry_interval", "6")
        conf.hosttemplatefactory.apply(self.host, "testtpl1")
        testserver1 = conf.hostsConf['testserver1']
        nagiosdirs = testserver1.get('nagiosSrvDirs')
        self.assertEquals(nagiosdirs['Interface eth0']['retry_interval'], "6",
                          "retry_interval=6")


# vim:set expandtab tabstop=4 shiftwidth=4:
