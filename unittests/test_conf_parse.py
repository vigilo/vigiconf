#!/usr/bin/env python
import sys, os, unittest, tempfile, shutil, glob, subprocess
from pprint import pprint

import conf
from lib.confclasses.host import Host


class ValidateDTD(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        self.dtddir = "../src/validation/dtd"
        self.hdir = "../src/conf.d/hosts"
        self.htdir = "../src/conf.d/hosttemplates"

    def test_host(self):
        """Validate the provided hosts against the DTD"""
        hosts = glob.glob(os.path.join(self.hdir, "*.xml"))
        for host in hosts:
            valid = subprocess.call(["xmllint", "--noout", "--dtdvalid",
                                    os.path.join(self.dtddir, "host.dtd"), host])
            assert valid == 0, "Validation of host \"%s\" failed" % os.path.basename(host)

    def test_hosttemplate(self):
        """Validate the provided hosttemplatess against the DTD"""
        hts = glob.glob(os.path.join(self.htdir, "*.xml"))
        for ht in hts:
            valid = subprocess.call(["xmllint", "--noout", "--dtdvalid",
                                    os.path.join(self.dtddir, "hosttemplate.dtd"), ht])
            assert valid == 0, "Validation of hosttemplate \"%s\" failed" % os.path.basename(ht)


class ParseHost(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        conf.confDir = "../src/conf.d"
        conf.dataDir = "../src"
        self.testdatadir = "testdata"
        ## Prepare temporary directory
        self.tmpdir = tempfile.mkdtemp(dir="/dev/shm")
        shutil.copytree(os.path.join(conf.confDir, "general"),
                        os.path.join(self.tmpdir, "general"))
        shutil.copytree(os.path.join(conf.confDir, "hosttemplates"),
                        os.path.join(self.tmpdir, "hosttemplates"))
        os.mkdir(os.path.join(self.tmpdir, "hosts"))
        conf.confDir = self.tmpdir
        conf.loadConf()
        #shutil.copy(os.path.join(self.testdatadir, "host.xml"), os.path.join(self.tmpdir, "hosts"))
        self.host = open(os.path.join(self.tmpdir, "hosts", "host.xml"), "w")

    def tearDown(self):
        """Call after every test case."""
        shutil.rmtree(self.tmpdir)


    def test_host(self):
        """Test the parsing of a basic host declaration"""
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" ip="192.168.1.1" group="Servers">
        </host>""")
        self.host.close()
        conf.loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        assert conf.hostsConf.has_key("testserver1"), \
                "host is not properly parsed"
        assert conf.hostsConf["testserver1"]["name"] == "testserver1", \
                "host name is not properly parsed"
        assert conf.hostsConf["testserver1"]["mainIP"] == "192.168.1.1", \
                "host IP is not properly parsed"
        assert conf.hostsConf["testserver1"]["serverGroup"] == "Servers", \
                "host main group is not properly parsed"

    def test_host_whitespace(self):
        """Test the handling of whitespaces in a basic host declaration"""
        self.host.write("""<?xml version="1.0"?>
        <host name=" testserver1 " ip=" 192.168.1.1 " group=" Servers ">
        </host>""")
        self.host.close()
        conf.loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        assert conf.hostsConf.has_key("testserver1"), \
                "host parsing does not handle whitespaces properly"

    def test_template(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" ip="192.168.1.1" group="Servers">
        <template>linux</template>
        </host>""")
        self.host.close()
        conf.loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        assert "Linux servers" in conf.hostsConf["testserver1"]["otherGroups"], \
                "The \"template\" tag is not properly parsed"

    def test_template_whitespace(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" ip="192.168.1.1" group="Servers">
        <template> linux </template>
        </host>""")
        self.host.close()
        try:
            conf.loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        except KeyError:
            self.fail("The \"template\" tag does not strip whitespaces")

    def test_attribute(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" ip="192.168.1.1" group="Servers">
        <attribute name="cpulist">2</attribute>
        </host>""")
        self.host.close()
        conf.loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        assert conf.hostsConf["testserver1"].has_key("cpulist") and \
                conf.hostsConf["testserver1"]["cpulist"] == "2", \
                "The \"attribute\" tag is not properly parsed"

    def test_attribute_whitespace(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" ip="192.168.1.1" group="Servers">
        <attribute name=" cpulist "> 2 </attribute>
        </host>""")
        self.host.close()
        conf.loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        assert conf.hostsConf["testserver1"].has_key("cpulist") and \
                conf.hostsConf["testserver1"]["cpulist"] == "2", \
                "The \"attribute\" tag parsing does not strip whitespaces"

    def test_tag_host(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" ip="192.168.1.1" group="Servers">
        <tag service="Host" name="important">2</tag>
        </host>""")
        self.host.close()
        conf.loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        assert "tags" in conf.hostsConf["testserver1"] and \
               "important" in conf.hostsConf["testserver1"]["tags"] and \
                conf.hostsConf["testserver1"]["tags"]["important"] == "2", \
                "The \"tag\" tag for hosts is not properly parsed"

    def test_tag_service(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" ip="192.168.1.1" group="Servers">
        <tag service="UpTime" name="important">2</tag>
        </host>""")
        self.host.close()
        conf.loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        assert "tags" in conf.hostsConf["testserver1"]["services"]["UpTime"] and \
               "important" in conf.hostsConf["testserver1"]["services"]["UpTime"]["tags"] and \
               conf.hostsConf["testserver1"]["services"]["UpTime"]["tags"]["important"] == "2", \
               "The \"tag\" tag for services is not properly parsed"

    def test_tag_whitespace(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" ip="192.168.1.1" group="Servers">
        <tag service=" Host " name=" important "> 2 </tag>
        </host>""")
        self.host.close()
        try:
            conf.loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        except KeyError:
            self.fail("The \"tag\" tag parsing does not strip whitespaces")
        assert "tags" in conf.hostsConf["testserver1"] and \
               "important" in conf.hostsConf["testserver1"]["tags"] and \
               conf.hostsConf["testserver1"]["tags"]["important"] == "2", \
               "The \"tag\" tag parsing does not strip whitespaces"

    def test_trap(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" ip="192.168.1.1" group="Servers">
        <trap service="test.add_trap" key="test.name">test.label</trap>
        </host>""")
        self.host.close()
        conf.loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        assert conf.hostsConf["testserver1"].has_key("trapItems") and \
                conf.hostsConf["testserver1"]["trapItems"]["test.add_trap"]["test.name"] == "test.label", \
                "The \"trap\" tag is not properly parsed"

    def test_trap_whitespace(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" ip="192.168.1.1" group="Servers">
        <trap service=" test.add_trap " key=" test.name "> test.label </trap>
        </host>""")
        self.host.close()
        conf.loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        assert "trapItems" in conf.hostsConf["testserver1"] and \
               "test.add_trap" in conf.hostsConf["testserver1"]["trapItems"] and \
               "test.name" in conf.hostsConf["testserver1"]["trapItems"]["test.add_trap"] and \
               conf.hostsConf["testserver1"]["trapItems"]["test.add_trap"]["test.name"] == "test.label", \
               "The \"trap\" tag parsing does not strip whitespaces"

    def test_group(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" ip="192.168.1.1" group="Servers">
        <group>Linux servers</group>
        </host>""")
        self.host.close()
        conf.loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        assert "Linux servers" in conf.hostsConf["testserver1"]["otherGroups"], \
                "The \"group\" tag is not properly parsed"

    def test_group_whitespace(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" ip="192.168.1.1" group="Servers">
        <group> Linux servers </group>
        </host>""")
        self.host.close()
        conf.loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        assert "Linux servers" in conf.hostsConf["testserver1"]["otherGroups"], \
                "The \"group\" tag parsing does not strip whitespaces"

    def test_test(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" ip="192.168.1.1" group="Servers">
        <test name="Interface">
            <arg name="label">eth0</arg>
            <arg name="ifname">eth0</arg>
        </test>
        </host>""")
        self.host.close()
        conf.loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        assert ('Interface eth0', 'service') in conf.hostsConf["testserver1"]["SNMPJobs"], \
                "The \"test\" tag is not properly parsed"

    def test_test_whitespace(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" ip="192.168.1.1" group="Servers">
        <test name=" Interface ">
            <arg name=" label "> eth0 </arg>
            <arg name=" ifname "> eth0 </arg>
        </test>
        </host>""")
        self.host.close()
        conf.loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        assert ('Interface eth0', 'service') in conf.hostsConf["testserver1"]["SNMPJobs"], \
                "The \"test\" tag parsing does not strip whitespaces"


class ParseHostTemplate(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        conf.confDir = "../src/conf.d"
        conf.dataDir = "../src"
        self.testdatadir = "testdata"
        ## Prepare temporary directory
        self.tmpdir = tempfile.mkdtemp(dir="/dev/shm")
        shutil.copytree(os.path.join(conf.confDir, "general"),
                        os.path.join(self.tmpdir, "general"))
        #shutil.copytree(os.path.join(conf.confDir, "hosttemplates"),
        #                os.path.join(self.tmpdir, "hosttemplates"))
        os.mkdir(os.path.join(self.tmpdir, "hosttemplates"))
        os.mkdir(os.path.join(self.tmpdir, "hosts"))
        conf.confDir = self.tmpdir
        conf.loadConf()
        conf.hosttemplatefactory.path = [os.path.join(self.tmpdir, "hosttemplates"),]
        #shutil.copy(os.path.join(self.testdatadir, "host.xml"), os.path.join(self.tmpdir, "hosts"))
        #self.host = open(os.path.join(self.tmpdir, "hosts", "host.xml"), "w")
        self.defaultht = open(os.path.join(self.tmpdir, "hosttemplates", "default.xml"), "w")
        self.defaultht.write('<?xml version="1.0"?>\n<template name="default"></template>')
        self.defaultht.close()
        self.ht = open(os.path.join(self.tmpdir, "hosttemplates", "test.xml"), "w")

    def tearDown(self):
        """Call after every test case."""
        shutil.rmtree(self.tmpdir)


    def test_template(self):
        """Test the parsing of a basic template declaration"""
        self.ht.write("""<?xml version="1.0"?>\n<template name="test"></template>""")
        self.ht.close()
        try:
            conf.hosttemplatefactory.load_templates()
        except KeyError:
            self.fail("template is not properly parsed")
        assert "test" in conf.hosttemplatefactory.templates, \
               "template is not properly parsed"

    def test_template_whitespace(self):
        self.ht.write("""<?xml version="1.0"?>\n<template name=" test "></template>""")
        self.ht.close()
        try:
            conf.hosttemplatefactory.load_templates()
        except KeyError:
            self.fail("template parsing does not strip whitespaces")
        assert "test" in conf.hosttemplatefactory.templates, \
               "template parsing does not strip whitespaces"

    def test_attribute(self):
        self.ht.write("""<?xml version="1.0"?>
                <template name="test">
                    <attribute name="testattr">testattrvalue</attribute>
                </template>""")
        self.ht.close()
        conf.hosttemplatefactory.load_templates()
        assert "testattr" in conf.hosttemplatefactory.templates["test"]["attributes"] and \
               conf.hosttemplatefactory.templates["test"]["attributes"]["testattr"] == "testattrvalue", \
               "The \"attribute\" tag is not properly parsed"

    def test_attribute_whitespace(self):
        self.ht.write("""<?xml version="1.0"?>
                <template name="test">
                    <attribute name=" testattr "> testattrvalue </attribute>
                </template>""")
        self.ht.close()
        conf.hosttemplatefactory.load_templates()
        assert "testattr" in conf.hosttemplatefactory.templates["test"]["attributes"] and \
               conf.hosttemplatefactory.templates["test"]["attributes"]["testattr"] == "testattrvalue", \
               "The \"attribute\" tag parsing does not strip whitespaces"

    def test_test(self):
        self.ht.write("""<?xml version="1.0"?>
                <template name="test">
                    <test name="TestTest"/>
                </template>""")
        self.ht.close()
        try:
            conf.hosttemplatefactory.load_templates()
        except KeyError:
            self.fail("The \"test\" tag is not properly parsed")
        assert {"name": "TestTest"} in conf.hosttemplatefactory.templates["test"]["tests"], \
               "The \"test\" tag is not properly parsed"

    def test_test_args(self):
        self.ht.write("""<?xml version="1.0"?>
                <template name="test">
                    <test name="TestTest">
                        <arg name="TestArg1">TestValue1</arg>
                        <arg name="TestArg2">TestValue2</arg>
                    </test>
                </template>""")
        self.ht.close()
        try:
            conf.hosttemplatefactory.load_templates()
        except KeyError:
            self.fail("The \"test\" tag with arguments is not properly parsed")
        assert len(conf.hosttemplatefactory.templates["test"]["tests"]) == 1 and \
               conf.hosttemplatefactory.templates["test"]["tests"][0]["name"] == "TestTest" and \
               "TestArg1" in conf.hosttemplatefactory.templates["test"]["tests"][0]["args"] and \
               "TestArg2" in conf.hosttemplatefactory.templates["test"]["tests"][0]["args"] and \
               conf.hosttemplatefactory.templates["test"]["tests"][0]["args"]["TestArg1"] == "TestValue1" and \
               conf.hosttemplatefactory.templates["test"]["tests"][0]["args"]["TestArg2"] == "TestValue2", \
               "The \"test\" tag with arguments is not properly parsed"

    def test_test_whitespace(self):
        self.ht.write("""<?xml version="1.0"?>
                <template name="test">
                    <test name=" TestTest ">
                        <arg name=" TestArg1 "> TestValue1 </arg>
                        <arg name=" TestArg2 "> TestValue2 </arg>
                    </test>
                </template>""")
        self.ht.close()
        try:
            conf.hosttemplatefactory.load_templates()
        except KeyError:
            self.fail("The \"test\" tag parsing does not strip whitespaces")
        assert len(conf.hosttemplatefactory.templates["test"]["tests"]) == 1 and \
               conf.hosttemplatefactory.templates["test"]["tests"][0]["name"] == "TestTest" and \
               "TestArg1" in conf.hosttemplatefactory.templates["test"]["tests"][0]["args"] and \
               "TestArg2" in conf.hosttemplatefactory.templates["test"]["tests"][0]["args"] and \
               conf.hosttemplatefactory.templates["test"]["tests"][0]["args"]["TestArg1"] == "TestValue1" and \
               conf.hosttemplatefactory.templates["test"]["tests"][0]["args"]["TestArg2"] == "TestValue2", \
               "The \"test\" tag parsing does not strip whitespaces"

    def test_group(self):
        self.ht.write("""<?xml version="1.0"?>
                <template name="test">
                    <group>Test group</group>
                </template>""")
        self.ht.close()
        conf.hosttemplatefactory.load_templates()
        assert "Test group" in conf.hosttemplatefactory.templates["test"]["groups"], \
               "The \"group\" tag is not properly parsed"

    def test_group_whitespace(self):
        self.ht.write("""<?xml version="1.0"?>
                <template name="test">
                    <group> Test group </group>
                </template>""")
        self.ht.close()
        conf.hosttemplatefactory.load_templates()
        assert "Test group" in conf.hosttemplatefactory.templates["test"]["groups"], \
               "The \"group\" tag parsing does not strip whitespaces"

    def test_parent(self):
        self.ht.write("""<?xml version="1.0"?>
            <templates>
                <template name="test1">
                </template>
                <template name="test2">
                    <parent>test1</parent>
                </template>
            </templates>""")
        self.ht.close()
        conf.hosttemplatefactory.load_templates()
        assert "test1" in conf.hosttemplatefactory.templates["test2"]["parent"], \
               "The \"parent\" tag is not properly parsed"

    def test_parent_whitespace(self):
        self.ht.write("""<?xml version="1.0"?>
            <templates>
                <template name="test1">
                </template>
                <template name="test2">
                    <parent> test1 </parent>
                </template>
            </templates>""")
        self.ht.close()
        try:
            conf.hosttemplatefactory.load_templates()
        except KeyError:
            self.fail("The \"parent\" tag parsing does not strip whitespaces")
        assert "test1" in conf.hosttemplatefactory.templates["test2"]["parent"], \
               "The \"parent\" tag parsing does not strip whitespaces"


# vim:set expandtab tabstop=4 shiftwidth=4:
