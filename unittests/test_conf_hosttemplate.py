#!/usr/bin/env python
import sys, os, unittest, tempfile, shutil, glob
from pprint import pprint

import conf
from lib.confclasses.hosttemplate import HostTemplate
from lib.confclasses.host import Host


class HostTemplates(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        conf.confDir = "../src/conf.d"
        conf.dataDir = "../src"
        # Load the configuration
        conf.loadConf()
        # We need to load the templates manually because we're adding a new
        # HostTemplate by hand. See the first lines of
        # HostTemplateFactory.apply() for details
        conf.hosttemplatefactory.load_templates()
        self.tpl = HostTemplate("testtpl1")
        self.host = Host("testserver1", "192.168.1.1", "Servers")

    def tearDown(self):
        """Call after every test case."""
        pass


    def test_add_test_simple(self):
        """Test for the add_test method, without test arguments"""
        self.tpl.add_test("UpTime")
        self.host.apply_template("testtpl1")
        assert conf.hostsConf["testserver1"]["services"].has_key("UpTime"), \
                "add_test does not work without test args"

    def test_add_test_args(self):
        """Test for the add_test method, with test arguments"""
        self.tpl.add_test("Interface", label="Loopback", name="lo")
        self.host.apply_template("testtpl1")
        assert conf.hostsConf["testserver1"]["SNMPJobs"][('Interface Loopback',
                'service')]["params"] == ["lo", "Loopback", "i"], \
                "add_test does not work with test args"

    def test_add_group_simple(self):
        """Test for the add_group method, with one argument only"""
        self.tpl.add_group("Test Group")
        self.host.apply_template("testtpl1")
        assert conf.hostsConf["testserver1"]["otherGroups"].has_key("Test Group"), \
                "add_group does not work with one arg"

    def test_add_group_multiple(self):
        """Test for the add_group method, with multiple arguments"""
        self.tpl.add_group("Test Group 1", "Test Group 2")
        self.host.apply_template("testtpl1")
        assert conf.hostsConf["testserver1"]["otherGroups"].has_key("Test Group 1"), \
                "add_group does not work with multiple args"
        assert conf.hostsConf["testserver1"]["otherGroups"].has_key("Test Group 2"), \
                "add_group does not work with multiple args"

    def test_add_attribute(self):
        """Test for the add_attribute method"""
        self.tpl.add_attribute("TestAttr", "TestVal")
        self.host.apply_template("testtpl1")
        assert conf.hostsConf["testserver1"]["TestAttr"] == "TestVal", \
                "add_attribute does not work"

    def test_inherit_test(self):
        self.tpl.add_test("UpTime")
        tpl2 = HostTemplate("testtpl2", "testtpl1")
        # Reload the templates
        conf.hosttemplatefactory.load_templates()
        assert "UpTime" in [ t["name"] for t in conf.hosttemplatefactory.templates["testtpl2"]["tests"] ], \
                "inheritance does not work with tests"

    def test_inherit_group(self):
        self.tpl.add_group("Test Group")
        tpl2 = HostTemplate("testtpl2", "testtpl1")
        # Reload the templates
        conf.hosttemplatefactory.load_templates()
        assert "Test Group" in conf.hosttemplatefactory.templates["testtpl2"]["groups"], \
                "inheritance does not work with groups"

    def test_inherit_attribute(self):
        self.tpl.add_attribute("TestAttr", "TestVal")
        tpl2 = HostTemplate("testtpl2", "testtpl1")
        # Reload the templates
        conf.hosttemplatefactory.load_templates()
        assert conf.hosttemplatefactory.templates["testtpl2"]["attributes"].has_key("TestAttr"), \
                "inheritance does not work with attributes"
        assert conf.hosttemplatefactory.templates["testtpl2"]["attributes"]["TestAttr"] == "TestVal", \
                "inheritance does not work with attributes"

    def test_inherit_redefine_test(self):
        self.tpl.add_test("Interface", name="eth0", label="Label1")
        tpl2 = HostTemplate("testtpl2", "testtpl1")
        tpl2.add_test("Interface", name="eth0", label="Label2")
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
        self.tpl.add_test("Interface", name="eth0", label="Label0")
        tpl2 = HostTemplate("testtpl2")
        tpl2.add_test("Interface", name="eth1", label="Label1")
        tpl3 = HostTemplate("testtpl3", ["testtpl1", "testtpl2"])
        # Reload the templates
        conf.hosttemplatefactory.load_templates()
        intftests = []
        for test in conf.hosttemplatefactory.templates["testtpl3"]["tests"]:
            if test["name"] == "Interface":
                intftests.append(test["args"]["name"])
        assert intftests == [ "eth0", "eth1"], \
                "multiple inheritance does not work (%s)" % str(intftests)

    def test_deepcopy(self):
        """
        If the template data from the parent is not copied with
        copy.deepcopy(), then the child's template data will propagate back
        into the parent
        """
        self.tpl.add_attribute("TestAttr1", "TestVal")
        tpl2 = HostTemplate("testtpl2", "testtpl1")
        tpl2.add_attribute("TestAttr2", "TestVal")
        # Reload the templates
        conf.hosttemplatefactory.load_templates()
        assert not conf.hosttemplatefactory.templates["testtpl1"]["attributes"].has_key("TestAttr2"), \
                "inheritence taints parent templates"

    def test_defined_templates(self):
        conf.hosttemplatefactory.load_templates()
        for tpl in conf.hosttemplatefactory.templates.keys():
            self.host.apply_template(tpl)

# vim:set expandtab tabstop=4 shiftwidth=4:
