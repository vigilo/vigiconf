#!/usr/bin/env python
import sys, os, unittest, tempfile, shutil, glob
from pprint import pprint

import conf
from lib.confclasses.host import Host


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

    def test_template(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" ip="192.168.1.1" group="Servers">
        <template name="linux"/>
        </host>""")
        self.host.close()
        conf.loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        assert "Linux servers" in conf.hostsConf["testserver1"]["otherGroups"], \
                "The \"template\" tag is not properly parsed"

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

    def test_tag_host(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" ip="192.168.1.1" group="Servers">
        <tag service="Host" name="important" value="2"/>
        </host>""")
        self.host.close()
        conf.loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        assert conf.hostsConf["testserver1"].has_key("tags") and \
                conf.hostsConf["testserver1"]["tags"]["important"] == "2", \
                "The \"tag\" tag for hosts is not properly parsed"

    def test_tag_service(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" ip="192.168.1.1" group="Servers">
        <tag service="UpTime" name="important" value="2"/>
        </host>""")
        self.host.close()
        conf.loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        assert conf.hostsConf["testserver1"]["services"]["UpTime"].has_key("tags") and \
                conf.hostsConf["testserver1"]["services"]["UpTime"]["tags"]["important"] == "2", \
                "The \"tag\" tag for services is not properly parsed"

    def test_trap(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" ip="192.168.1.1" group="Servers">
        <trap service="test.add_trap" key="test.name" value="test.label"/>
        </host>""")
        self.host.close()
        conf.loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        assert conf.hostsConf["testserver1"].has_key("trapItems") and \
                conf.hostsConf["testserver1"]["trapItems"]["test.add_trap"]["test.name"] == "test.label", \
                "The \"trap\" tag is not properly parsed"

    def test_group(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" ip="192.168.1.1" group="Servers">
        <group name="Linux servers"/>
        </host>""")
        self.host.close()
        conf.loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        assert "Linux servers" in conf.hostsConf["testserver1"]["otherGroups"], \
                "The \"group\" tag is not properly parsed"

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


# vim:set expandtab tabstop=4 shiftwidth=4:
