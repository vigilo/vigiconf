# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# pylint: disable-msg=C0111,W0211,R0904
# Copyright (C) 2006-2020 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>
from __future__ import absolute_import, print_function

import os, unittest, shutil, socket
from xml.etree import ElementTree as ET

from vigilo.common.conf import settings

from vigilo.vigiconf.lib.confclasses.test import Test, TestFactory
from vigilo.vigiconf.discoverator import Discoverator

from .helpers import setup_tmpdir, setup_db, teardown_db, TESTDATADIR


class TestDiscoveratorBasics(unittest.TestCase):

    def setUp(self):
        setup_db()
        self.tmpdir = setup_tmpdir()
        testfactory = TestFactory(confdir=settings["vigiconf"].get("confdir"))
        self.disc = Discoverator(testfactory, group="Test")
        self.disc.testfactory.load_hclasses_checks()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        teardown_db()

    def test_snmp_novalue(self):
        tmpfile = os.path.join(self.tmpdir, "test.walk")
        walkfile = open(tmpfile, "w")
        walkfile.write(".1.3.6.1.2.1.2.2.1.6.1 = \n")
        walkfile.close()
        self.disc._get_snmp_command = lambda c, v, h: ["cat", tmpfile]
        try:
            self.disc.scanhost("test", "public", "v2c")
        except ValueError:
            self.fail("Discoverator chokes on empty SNMP values")

    def test_snmp_empty(self):
        """Discoverator should handle empty walks"""
        tmpfile = os.path.join(self.tmpdir, "test.walk")
        open(tmpfile, "w").close()
        self.disc._get_snmp_command = lambda c, v, h: ["cat", tmpfile]
        try:
            self.disc.scanhost("test", "public", "v2c")
        except (ValueError, TypeError):
            self.fail("Discoverator chokes on empty SNMP walks")
        print(self.disc.oids)
        self.assertEqual(len(self.disc.oids), 0)

    def test_wrapped_line(self):
        """Discoverator : valeur multiligne sans guillemets"""
        tmpfile = os.path.join(self.tmpdir, "test.walk")
        walkfile = open(tmpfile, "w")
        walkfile.write(".1.42 = First line\nSecond line\nThird line\n")
        walkfile.close()
        self.disc._get_snmp_command = lambda c, v, h: ["cat", tmpfile]
        self.disc.scanhost("test", "public", "v2c")
        self.assertEqual(self.disc.oids[".1.42"],
                    "First line\nSecond line\nThird line\n")

    def test_wrapped_line2(self):
        """Discoverator : valeur multiligne entre guillemets"""
        tmpfile = os.path.join(self.tmpdir, "test.walk")
        walkfile = open(tmpfile, "w")
        walkfile.write(".1.42 = \"First line\nSecond line\nThird line\n\"")
        walkfile.close()
        self.disc._get_snmp_command = lambda c, v, h: ["cat", tmpfile]
        self.disc.scanhost("test", "public", "v2c")
        self.assertEqual(self.disc.oids[".1.42"],
                    "First line\nSecond line\nThird line\n")


class DiscoveratorBaseTest(object):
    testmib = None

    def setUp(self):
        setup_db()
        self.tmpdir = setup_tmpdir()
        testfactory = TestFactory(confdir=settings["vigiconf"].get("confdir"))
        self.disc = Discoverator(testfactory, group="Test")
        self.disc.testfactory.load_hclasses_checks()
        walkfile = os.path.join(TESTDATADIR, "discoverator", self.testmib)
        self.disc.scanfile(walkfile)
        self.disc.detect()
        self.testnames = [ t["name"] for t in self.disc.tests ]
        print("Detected tests:", self.testnames)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        teardown_db()

    def test_hostname(self):
        expected = socket.getfqdn("localhost")
        self.assertEqual(self.disc.hostname, expected,
            "Hostname not detected correctly (got %s)" % self.disc.hostname)

    def test_ipaddr(self):
        self.assertEqual(self.disc.ipaddr, "127.0.0.1",
            "IP not detected correcty (got %s)" % self.disc.ipaddr)


class DiscoveratorLinux(DiscoveratorBaseTest, unittest.TestCase):
    testmib = "linux.walk"

    def test_simple_test_detection(self):
        """Test the simple test detection on Linux
        This uses the test's detect_oid() method"""
        for test in [ "ucd.Load", "ucd.CPU", "all.TotalProcesses",
                      "all.Users", "ucd.RAM", "all.UpTime", "all.Swap",
                      "all.Partition", "all.Interface" ]:
            self.assertTrue(test in self.testnames,
                            "Test %s is not detected" % test)
        self.assertFalse("all.RAM" in self.testnames, "Test all.RAM is detected")

    def test_partition_args(self):
        """Test the args of the Partition test detection on Linux"""
        args = []
        for testdict in self.disc.tests:
            if testdict["name"] != "all.Partition":
                continue
            args.append(testdict['args'])
        goodargs = [[
                        ("label", "/"),
                        ("partname", "/",)
                    ], [
                        ("label", "/mnt/fake"),
                        ("partname", "/mnt/fake"),
                    ], [
                        ("label", "/var"),
                        ("partname", "/var"),
                    ]]
        self.assertEqual(args, goodargs,
                         "Arguments are not properly detected:\n%s\n%s"
                         % (str(args), str(goodargs)))

    def test_interface_args(self):
        """Test the args of the Interface test detection on Linux"""
        args = []
        for testdict in self.disc.tests:
            if testdict["name"] != "all.Interface":
                continue
            args.append(testdict["args"])
        goodargs = [[
                        ("counter32", "False"),
                        ("ifname", "eth0"),
                        ("label", "eth0"),
                    ], [
                        ("counter32", "False"),
                        ("ifname", "eth1"),
                        ("label", "eth1"),
                   ]]
        self.assertEqual(args, goodargs,
                         "Arguments are not properly detected:\n%s\n%s"
                         % (str(args), str(goodargs)))


class DiscoveratorSpecificTest(unittest.TestCase):
    testmib = "linux.walk"

    def setUp(self):
        setup_db()
        self.tmpdir = setup_tmpdir()
        testfactory = TestFactory(confdir=settings["vigiconf"].get("confdir"))
        self.disc = Discoverator(testfactory, group="Test")
        self.disc.testfactory.load_hclasses_checks()
        walkfile = os.path.join(TESTDATADIR, "discoverator", self.testmib)
        self.disc.scanfile(walkfile)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        teardown_db()

    def test_multiple_test_detection(self):
        """Teste la détection de plusieurs tests pour Linux
        This uses the test's detect_oid() method"""
        self.disc.detect(["Swap", "Partition", "Interface"])
        self.testnames = [ t["name"] for t in self.disc.tests ]

        for test in [ "all.Swap", "all.Partition", "all.Interface" ]:
            self.assertTrue(test in self.testnames,
                            "Test %s is not detected" % test)

    def test_single_test_detection(self):
        """Teste la détection d'un test unique pour Linux
        This uses the test's detect_oid() method"""
        self.disc.detect([ "Partition" ])
        self.testnames = [ t["name"] for t in self.disc.tests ]

        self.assertTrue("all.Partition" in self.testnames,
                "Test %s is not detected" % "Partition")
        self.assertFalse("all.Interface" in self.testnames,
                "Test %s is detected" % "Interface")
