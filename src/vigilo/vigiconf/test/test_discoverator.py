#!/usr/bin/env python
import os, unittest, shutil, socket

from vigilo.vigiconf.discoverator import Discoverator

from helpers import setup_tmpdir, setup_db, teardown_db

class TestDiscoveratorBasics(unittest.TestCase):
    testmib = None

    def setUp(self):
        """Call before every test case."""
        setup_db()
        self.tmpdir = setup_tmpdir()
        self.disc = Discoverator(group="Test")
        if self.testmib:
            walkfile = os.path.join(os.path.dirname(__file__), "testdata",
                                    "discoverator", self.testmib)
            self.disc.scanfile(walkfile)
            self.disc.detect()
        self.testnames = [ t["name"] for t in self.disc.tests ]

    def tearDown(self):
        """Call after every test case."""
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
        assert self.disc.hclasses == set(["all", "ucd", "linux"]), \
               "Host classes are not properly detected: %s" \
               % str(self.disc.hclasses)

    def test_simple_test_detection(self):
        """Test the simple test detection on Linux
        This uses the test's detect_oid() method"""
        for test in [ "Load", "CPU", "TotalProcesses", "Users", "RAM",
                      "UpTime", "Swap", "Partition", "Interface" ]:
            assert test in self.testnames, "Test %s is not detected" % test

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
        assert args == goodargs, \
            "Arguments are not properly detected:\n%s\n%s" \
            % (str(args), str(goodargs))

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
        assert args == goodargs, \
            "Arguments are not properly detected:\n%s\n%s" \
            % (str(args), str(goodargs))


class DiscoveratorSolaris(TestDiscoveratorBasics):
    testmib = "solaris.walk"

    def test_classes(self):
        """Test the host classes detection on Solaris"""
        assert self.disc.hclasses == set(["all", "ucd", "solaris"]), \
               "Host classes are not properly detected: %s" \
               % str(self.disc.hclasses)

    def test_simple_test_detection(self):
        """Test the simple test detection on Solaris
        This uses the test's detect_oid() method"""
        for test in [ "Load", "CPU", "TotalProcesses", "Users", "RAM",
                      "UpTime", "Swap", "TCPConn", "Partition", "Interface" ]:
            assert test in self.testnames, "Test %s is not detected" % test

    def test_partition_args(self):
        """Test the args of the Partition test detection on Solaris"""
        args = []
        for testdict in self.disc.tests:
            if testdict["name"] != "Partition":
                continue
            args.append({ "partname": testdict["args"]["partname"],
                          "label": testdict["args"]["label"] })
        goodargs = [
                    {"partname": "/",
                     "label": "/"},
                    {"partname": "/data",
                     "label": "/data"},
                    {"partname": "/opt",
                     "label": "/opt"},
                    {"partname": "/outils/Microtec86",
                     "label": "/outils/Microtec86"},
                    {"partname": "/outils/ilog4.0",
                     "label": "/outils/ilog4.0"},
                    {"partname": "/tmp",
                     "label": "/tmp"},
                    {"partname": "/usr",
                     "label": "/usr"},
                    {"partname": "/var",
                     "label": "/var"},
                    {"partname": "/var/run",
                     "label": "/var/run"},
                   ]
        args.sort()
        goodargs.sort()
        assert args == goodargs, \
            "Arguments are not properly detected:\n%s\n%s" \
            % (str(args), str(goodargs))

    def test_interface_args(self):
        """Test the args of the Interface test detection on Solaris"""
        args = []
        for testdict in self.disc.tests:
            if testdict["name"] != "Interface":
                continue
            args.append({ "ifname": testdict["args"]["ifname"],
                          "label": testdict["args"]["label"] })
        goodargs = [
                    {"ifname": "eri0",
                     "label": "eri0"},
                   ]
        args.sort()
        goodargs.sort()
        assert args == goodargs, \
            "Arguments are not properly detected:\n%s\n%s" \
            % (str(args), str(goodargs))



class DiscoveratorWinHP(TestDiscoveratorBasics):
    testmib = "winhp.walk"

    def test_classes(self):
        """Test the host classes detection on Windows/HP"""
        assert self.disc.hclasses == set(["all", "windows", "hp-insight"]), \
               "Host classes are not properly detected: %s" \
               % str(self.disc.hclasses)

    def test_simple_test_detection(self):
        """Test the simple test detection on Windows/HP
        This uses the test's detect_oid() method"""
        for test in [ "Load", "CPU", "TotalProcesses", "Users", "RAM",
                      "UpTime", "Swap", "TCPConn", "RAID", "Fans",
                      "Temperature", "Partition", "Interface", "DiskIO" ]:
            assert test in self.testnames, "Test %s is not detected" % test

    def test_partition_args(self):
        """Test the args of the Partition test detection on Windows/HP"""
        args = []
        for testdict in self.disc.tests:
            if testdict["name"] != "Partition":
                continue
            args.append({ "partname": testdict["args"]["partname"],
                          "label": testdict["args"]["label"] })
        goodargs = [
                    {"partname": "C:.*",
                     "label": "C: Label:  Serial Number 606d8c65"},
                    {"partname": "D:.*",
                     "label": "D: Label:Data  Serial Number e42532eb"},
                   ]
        args.sort()
        goodargs.sort()
        assert args == goodargs, \
            "Arguments are not properly detected:\n%s\n%s" \
            % (str(args), str(goodargs))

    def test_interface_args(self):
        """Test the args of the Interface test detection on Windows/HP"""
        args = []
        for testdict in self.disc.tests:
            if testdict["name"] != "Interface":
                continue
            args.append({ "ifname": testdict["args"]["ifname"],
                          "label": testdict["args"]["label"] })
        goodargs = [
                    {"ifname": "HP NC7782 Gigabit Server Adapter",
                     "label": "HP NC7782 Gigabit Server Adapter"},
                   ]
        args.sort()
        goodargs.sort()
        assert args == goodargs, \
            "Arguments are not properly detected:\n%s\n%s" \
            % (str(args), str(goodargs))

    def test_diskio_args(self):
        """Test the args of the DiskIO test detection on Windows/HP"""
        args = []
        for testdict in self.disc.tests:
            if testdict["name"] != "DiskIO":
                continue
            args.append({ "diskname": testdict["args"]["diskname"] })
        print args
        goodargs = [{"diskname": "Disk 0|1.1"}]
        args.sort()
        goodargs.sort()
        assert args == goodargs, \
            "Arguments are not properly detected:\n%s\n%s" \
            % (str(args), str(goodargs))


class DiscoveratorCisco(TestDiscoveratorBasics):
    testmib = "cisco.walk"

    def test_classes(self):
        """Test the host classes detection on Cisco"""
        assert self.disc.hclasses == set(["all", "cisco"]), \
               "Host classes are not properly detected: %s" \
               % str(self.disc.hclasses)

    def test_simple_test_detection(self):
        """Test the simple test detection on Cisco
        This uses the test's detect_oid() method"""
        for test in [ "CPU", "RAM", "Temperature", "TCPConn", "Power",
                      "Fans", "UpTime", "Interface" ]:
            assert test in self.testnames, "Test %s is not detected" % test

    def test_interface_args(self):
        """Test the args of the Interface test detection on Cisco"""
        args = []
        for testdict in self.disc.tests:
            if testdict["name"] != "Interface":
                continue
            args.append({ "ifname": testdict["args"]["ifname"],
                          "label": testdict["args"]["label"] })
        goodargs = []
        for index in range(1, 13):
            goodargs.append( {"ifname": "FastEthernet0/%s" % index,
                           "label": "FE0/%s" % index,
                          } )
        goodargs.append( {"ifname": "Vlan1", "label": "Vlan1"} )
        args.sort()
        goodargs.sort()
        assert args == goodargs, \
            "Arguments are not properly detected:\n%s\n%s" \
            % (str(args), str(goodargs))

    def test_attribute_tempsensors(self):
        """Test the tempsensors attribute detection on Cisco"""
        assert self.disc.attributes.has_key("tempsensors"), \
            "Argument tempsensors is not detected"
        assert self.disc.attributes["tempsensors"] == ["chassis"], \
            "Argument tempsensors is not detected properly"

class DiscoveratorExpand(TestDiscoveratorBasics):
    testmib = "expand.walk"

    def test_classes(self):
        """Test the host classes detection on Expand"""
        assert self.disc.hclasses == set(["all", "expand", "ucd"]), \
               "Host classes are not properly detected: %s" \
               % str(self.disc.hclasses)

    def test_simple_test_detection(self):
        """Test the simple test detection on Cisco
        This uses the test's detect_oid() method"""
        for test in [ "Interface", "UpTime", "CPU", "Load", "TCPConn", "RAM" ]:
            assert test in self.testnames, "Test %s is not detected" % test

class DiscoveratorAlcatel(TestDiscoveratorBasics):
    testmib = "alcatel.walk"

    def test_classes(self):
        """Test the host classes detection on Alcatel"""
        assert self.disc.hclasses == set(["all", "alcatel"]), \
               "Host classes are not properly detected: %s" \
               % str(self.disc.hclasses)

    def test_simple_test_detection(self):
        """Test the simple test detection on Alcatel
        This uses the test's detect_oid() method"""
        for test in [ "Interface", "Temperature", "TCPConn", "RAM", "UpTime",
                      "Fans", "CPU" ]:
            assert test in self.testnames, "Test %s is not detected" % test


# vim:set expandtab tabstop=4 shiftwidth=4:
