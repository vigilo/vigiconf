# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# pylint: disable-msg=C0111,W0211,R0904
# Copyright (C) 2006-2011 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

import os, unittest, shutil, socket

from vigilo.common.conf import settings

from vigilo.vigiconf.lib.confclasses.test import TestFactory
from vigilo.vigiconf.discoverator import Discoverator

from helpers import setup_tmpdir, setup_db, teardown_db, TESTDATADIR


class TestDiscoveratorBasics(unittest.TestCase):
    testmib = None

    def setUp(self):
        setup_db()
        self.tmpdir = setup_tmpdir()
        testfactory = TestFactory(confdir=settings["vigiconf"].get("confdir"))
        self.disc = Discoverator(testfactory, group="Test")
        self.disc.testfactory.load_hclasses_checks()
        if self.testmib:
            walkfile = os.path.join(TESTDATADIR, "discoverator", self.testmib)
            self.disc.scanfile(walkfile)
            self.disc.detect()
        self.testnames = [ t["name"] for t in self.disc.tests ]

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        teardown_db()

    def test_hostname(self):
        if self.testmib:
            expected = socket.getfqdn("localhost")
            self.assertEqual(self.disc.hostname, expected,
                "Hostname not detected correctly (got %s)" % self.disc.hostname)

    def test_ipaddr(self):
        if self.testmib:
            self.assertEqual(self.disc.ipaddr, "127.0.0.1",
                "IP not detected correcty (got %s)" % self.disc.ipaddr)

    def test_snmp_novalue(self):
        tmpfile = os.path.join(self.tmpdir, "test.walk")
        walkfile = open(tmpfile, "w")
        walkfile.write(".1.3.6.1.2.1.2.2.1.6.1 = \n")
        walkfile.close()
        self.disc.snmpcommand = "cat %s" % tmpfile
        try:
            self.disc.scanhost("test")
        except ValueError:
            self.fail("Discoverator chokes on empty SNMP values")


class DiscoveratorLinux(TestDiscoveratorBasics):
    testmib = "linux.walk"

    def test_classes(self):
        """Test the host classes detection on Linux"""
        self.assertEqual(self.disc.hclasses, set(["all", "ucd", "linux"]),
               "Host classes are not properly detected: %s"
               % str(self.disc.hclasses))

    def test_simple_test_detection(self):
        """Test the simple test detection on Linux
        This uses the test's detect_oid() method"""
        for test in [ "Load", "CPU", "TotalProcesses", "Users", "RAM",
                      "UpTime", "Swap", "Partition", "Interface" ]:
            self.assertTrue(test in self.testnames,
                            "Test %s is not detected" % test)

    def test_partition_args(self):
        """Test the args of the Partition test detection on Linux"""
        args = []
        for testdict in self.disc.tests:
            if testdict["name"] != "Partition":
                continue
            args.append({ "partname": testdict["args"]["partname"],
                          "label": testdict["args"]["label"] })
        goodargs = [
                    {"partname": "/",
                     "label": "/"},
                    {"partname": "/mnt/fake",
                     "label": "/mnt/fake"},
                    {"partname": "/var",
                     "label": "/var"},
                   ]
        args.sort()
        goodargs.sort()
        self.assertEqual(args, goodargs,
                         "Arguments are not properly detected:\n%s\n%s"
                         % (str(args), str(goodargs)))

    def test_interface_args(self):
        """Test the args of the Interface test detection on Linux"""
        args = []
        for testdict in self.disc.tests:
            if testdict["name"] != "Interface":
                continue
            args.append({ "ifname": testdict["args"]["ifname"],
                          "label": testdict["args"]["label"] })
        goodargs = [
                    {"ifname": "eth0",
                     "label": "eth0"},
                    {"ifname": "eth1",
                     "label": "eth1"},
                   ]
        args.sort()
        goodargs.sort()
        self.assertEqual(args, goodargs,
                         "Arguments are not properly detected:\n%s\n%s"
                         % (str(args), str(goodargs)))

