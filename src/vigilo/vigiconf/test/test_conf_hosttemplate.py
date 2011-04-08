# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# pylint: disable-msg=C0111,W0212,R0904

import unittest

from vigilo.common.conf import settings

import vigilo.vigiconf.conf as conf
from vigilo.vigiconf.lib.confclasses.test import TestFactory
from vigilo.vigiconf.lib.confclasses.hosttemplate import HostTemplate
from vigilo.vigiconf.lib.confclasses.hosttemplate import HostTemplateFactory
from vigilo.vigiconf.lib.confclasses.host import Host

from helpers import setup_db, teardown_db


class HostTemplates(unittest.TestCase):

    def setUp(self):
        setup_db()
        testfactory = TestFactory(confdir=settings["vigiconf"]["confdir"])
        self.hosttemplatefactory = HostTemplateFactory(testfactory)
        self.hosttemplatefactory.register(HostTemplate("default"))
        self.tpl = HostTemplate("testtpl1")
        self.hosttemplatefactory.register(self.tpl)
        conf.hostsConf = {}
        self.host = Host(conf.hostsConf, "dummy", "testserver1",
                         "192.168.1.1", "Servers")

    def tearDown(self):
        conf.hostsConf = {}
        teardown_db()


    def test_add_test_simple(self):
        """Test for the add_test method, without test arguments"""
        self.tpl.add_test("UpTime")
        self.hosttemplatefactory.apply(self.host, "testtpl1")
        self.assertTrue(conf.hostsConf["testserver1"]["services"].has_key(
                        "UpTime"), "add_test does not work without test args")

    def test_add_test_args(self):
        """Test for the add_test method, with test arguments"""
        self.tpl.add_test("Interface", {"label":"Loopback", "ifname":"lo"})
        self.hosttemplatefactory.apply(self.host, "testtpl1")
        self.assertTrue(conf.hostsConf["testserver1"]["SNMPJobs"]
                [('Interface Loopback', 'service')]["params"]
                == ["lo", "Loopback", "i"],
                "add_test does not work with test args")

    def test_add_group_simple(self):
        """Test for the add_group method, with one argument only"""
        self.tpl.add_group("/Test Group")
        self.hosttemplatefactory.apply(self.host, "testtpl1")
        self.assertTrue("/Test Group" in
                conf.hostsConf["testserver1"]["otherGroups"],
                "add_group does not work with one arg")

    def test_add_group_multiple(self):
        """Test for the add_group method, with multiple arguments"""
        self.tpl.add_group("/Test Group 1", "/Test Group 2")
        self.hosttemplatefactory.apply(self.host, "testtpl1")
        self.assertTrue("/Test Group 1" in
                conf.hostsConf["testserver1"]["otherGroups"],
                "add_group does not work with multiple args")
        self.assertTrue("/Test Group 2" in
                conf.hostsConf["testserver1"]["otherGroups"],
                "add_group does not work with multiple args")

    def test_add_attribute(self):
        """Test for the add_attribute method"""
        self.tpl.add_attribute("TestAttr", "TestVal")
        self.hosttemplatefactory.apply(self.host, "testtpl1")
        self.assertEqual(conf.hostsConf["testserver1"]["TestAttr"],
                         "TestVal", "add_attribute does not work")

    def test_inherit_test(self):
        self.tpl.add_test("UpTime")
        tpl2 = HostTemplate("testtpl2")
        tpl2.add_parent("testtpl1")
        self.hosttemplatefactory.register(tpl2)
        # Reload the templates
        self.hosttemplatefactory.load_templates()
        testnames = [ t["name"] for t in
                self.hosttemplatefactory.templates["testtpl2"]["tests"] ]
        self.assertTrue("UpTime" in testnames,
                        "inheritance does not work with tests")

    def test_inherit_group(self):
        self.tpl.add_group("Test Group")
        tpl2 = HostTemplate("testtpl2")
        tpl2.add_parent("testtpl1")
        self.hosttemplatefactory.register(tpl2)
        # Reload the templates
        self.hosttemplatefactory.load_templates()
        self.assertTrue("Test Group" in
                self.hosttemplatefactory.templates["testtpl2"]["groups"],
                "inheritance does not work with groups")

    def test_inherit_attribute(self):
        self.tpl.add_attribute("TestAttr", "TestVal")
        tpl2 = HostTemplate("testtpl2")
        tpl2.add_parent("testtpl1")
        self.hosttemplatefactory.register(tpl2)
        # Reload the templates
        self.hosttemplatefactory.load_templates()
        tpldata = self.hosttemplatefactory.templates["testtpl2"]
        self.assertTrue(tpldata["attributes"].has_key("TestAttr"),
                "inheritance does not work with attributes")
        self.assertEqual(tpldata["attributes"]["TestAttr"], "TestVal",
                "inheritance does not work with attributes")

    def test_inherit_redefine_test(self):
        self.tpl.add_test("Interface", {"ifname":"eth0", "label":"Label1"})
        tpl2 = HostTemplate("testtpl2")
        tpl2.add_parent("testtpl1")
        tpl2.add_test("Interface", {"ifname":"eth0", "label":"Label2"})
        self.hosttemplatefactory.register(tpl2)
        # Reload the templates
        self.hosttemplatefactory.load_templates()
        intftest = None
        for test in self.hosttemplatefactory.templates["testtpl2"]["tests"]:
            if test["name"] == "Interface":
                intftest = test
        self.assertTrue(intftest is not None,
                        "inheritance does not work with tests")
        self.assertEqual(intftest["args"]["label"], "Label2",
                "child templates cannot redefine tests from parent templates")

    def test_inherit_multiple_test(self):
        self.tpl.add_test("Interface", {"ifname":"eth0", "label":"Label0"})
        tpl2 = HostTemplate("testtpl2")
        tpl2.add_test("Interface", {"ifname":"eth1", "label":"Label1"})
        self.hosttemplatefactory.register(tpl2)
        tpl3 = HostTemplate("testtpl3")
        tpl3.add_parent(["testtpl1", "testtpl2"])
        self.hosttemplatefactory.register(tpl3)
        # Reload the templates
        self.hosttemplatefactory.load_templates()
        intftests = []
        for test in self.hosttemplatefactory.templates["testtpl3"]["tests"]:
            if test["name"] == "Interface":
                intftests.append(test["args"]["ifname"])
        self.assertEqual(intftests, [ "eth0", "eth1"],
                "multiple inheritance does not work (%s)" % str(intftests))

    def test_deepcopy(self):
        """
        Test de la copie en profondeur
        If the template data from the parent is not copied with
        copy.deepcopy(), then the child's template data will propagate back
        into the parent
        """
        self.tpl.add_attribute("TestAttr1", "TestVal")
        tpl2 = HostTemplate("testtpl2")
        tpl2.add_parent("testtpl1")
        tpl2.add_attribute("TestAttr2", "TestVal")
        self.hosttemplatefactory.register(tpl2)
        # Reload the templates
        self.hosttemplatefactory.load_templates()
        tpldata = self.hosttemplatefactory.templates["testtpl1"]
        self.failIf(tpldata["attributes"].has_key("TestAttr2"),
                "inheritence taints parent templates")

    def test_defined_templates(self):
        self.hosttemplatefactory.load_templates()
        for tpl in self.hosttemplatefactory.templates.keys():
            self.hosttemplatefactory.apply(self.host, tpl)

    def test_parent_default(self):
        tpl1 = HostTemplate("testtpl2")
        tpl1.add_parent("testtpl1")
        self.hosttemplatefactory.register(tpl1)
        self.assertTrue("default" in
                self.hosttemplatefactory.templates["testtpl1"]["parent"],
                "The \"default\" template is not automatically added as "
                "parent to other templates")


    def test_add_nagios_directive(self):
        """Test for the add_nagios_directive method"""
        self.tpl.add_nagios_directive("max_check_attempts", "5")
        tpldata = self.hosttemplatefactory.templates["testtpl1"]
        self.assertEquals(tpldata["nagiosDirectives"]["max_check_attempts"],
                          "5")



    def test_add_nagios_service_directive(self):
        """Test for the add_nagios_service_directive method"""
        self.tpl.add_nagios_service_directive("Interface eth1",
                "retry_interval", "10")
        tpldata = self.hosttemplatefactory.templates["testtpl1"]
        self.assertEquals(tpldata["nagiosSrvDirs"]["Interface eth1"]
                          ["retry_interval"], "10")

    def test_nagiosdirs_apply_on_host(self):
        self.tpl.add_nagios_directive("retry_interval", "8")
        self.hosttemplatefactory.apply(self.host, "testtpl1")
        testserver1 = conf.hostsConf['testserver1']
        nagiosdirs = testserver1.get('nagiosDirectives')
        self.assertEquals(nagiosdirs['retry_interval'], "8",
                          "retry_interval=8")

    def test_nagios_srvdirs_apply_on_host(self):
        self.tpl.add_nagios_service_directive("Interface eth0", "retry_interval", "6")
        self.hosttemplatefactory.apply(self.host, "testtpl1")
        testserver1 = conf.hostsConf['testserver1']
        nagiosdirs = testserver1.get('nagiosSrvDirs')
        self.assertEquals(nagiosdirs['Interface eth0']['retry_interval'], "6",
                          "retry_interval=6")


