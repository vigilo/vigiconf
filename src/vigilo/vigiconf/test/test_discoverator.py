# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# pylint: disable-msg=C0111,W0211,R0904
# Copyright (C) 2006-2013 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>
from __future__ import absolute_import

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
        self.testnames = [ t["name"] for t in self.disc.tests ]

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
        print self.disc.oids
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

    def test_detect_hclasses_wrapped_line(self):
        self.disc.oids[".1.3.6.1.2.1.1.1.0"] = "l1\nTest HClass\nl3\n"
        self.disc.testfactory.tests["faketest"] = {"test_hclass": None}
        self.disc.testfactory.hclasschecks["test_hclass"] = {
                "sysdescr": ".*Test HClass.*"}
        self.disc.find_hclasses_sysdescr()
        print self.disc.hclasses
        self.assertTrue("test_hclass" in self.disc.hclasses)

    def test_detect_homonyms(self):
        """
        Détection des tests avec homonymie.

        Si plusieurs classes d'hôtes fournissent le même test avec une méthode
        de détection, chacune de ces méthodes de détection doit être appelée.
        """
        class FakeTest(Test):
            oids = [".1.3.6.1.2.1.1.1.0"]
        class FakeTest2(FakeTest):
            pass
        # On fait en sorte que les 2 tests soient vus
        # comme ayant le même nom.
        FakeTest2.__name__ = FakeTest.__name__
        self.disc.oids[".1.3.6.1.2.1.1.1.0"] = ""
        self.disc.testfactory.tests["faketest"] = {
            "testclass1": FakeTest,
            "testclass2": FakeTest2,
        }
        self.disc.find_tests()
        self.disc.find_hclasses()
        self.assertTrue("testclass1" in self.disc.hclasses,
            str(self.disc.hclasses))
        self.assertTrue("testclass2" in self.disc.hclasses,
            str(self.disc.hclasses))
        # Il ne doit y avoir qu'un seul test dans le résultat
        self.disc.deduplicate_tests()
        decl = self.disc.declaration()
        testlines = []
        for elem in decl:
            if elem.tag != "test":
                continue
            testlines.append(ET.tostring(elem))
        self.assertEqual(testlines, ['<test name="FakeTest" />'])


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
        """Test the simple test detection on Linux
        This uses the test's detect_oid() method"""
        self.disc.detect(["Swap", "Partition", "Interface"])
        self.testnames = [ t["name"] for t in self.disc.tests ]

        for test in [ "Swap", "Partition", "Interface" ]:
            self.assertTrue(test in self.testnames,
                            "Test %s is not detected" % test)

    def test_single_test_detection(self):
        """Test the simple test detection on Linux
        This uses the test's detect_oid() method"""
        self.disc.detect([ "Partition" ])
        self.testnames = [ t["name"] for t in self.disc.tests ]

        self.assertTrue("Partition" in self.testnames,
                "Test %s is not detected" % "Partition")
        self.assertFalse("Interface" in self.testnames,
                "Test %s is detected" % "Interface")
