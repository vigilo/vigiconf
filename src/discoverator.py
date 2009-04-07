#!/usr/bin/env python
################################################################################
#
# Copyright (C) 2007-2009 CS-SI
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
################################################################################

"""
This module contains the Discoverator, a tool to generate the supervision
configuation of a host by analysing its SNMP MIB.
"""

import os
import sys
import subprocess
import re
import socket
from optparse import OptionParser
#from pprint import pprint

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import conf


class DiscoveratorError(Exception):
    """Error during the Discoverator process"""
    pass

class Discoverator(object):
    """
    Scan a host or file containing the hosts' SNMP walk to find the host
    classes and the available tests.
    Also extract information about the host (number of CPUs, etc...)
    """

    def __init__(self, group=None):
        self.group = group
        self.oids = {}
        self.hclasses = set()
        self.tests = []
        self.hostname = None
        self.ipaddr = None
        self.attributes = {}
        conf.testfactory.load_hclasses_checks()

    def scanfile(self, filename):
        """
        Use the stored SNMP walk.
        It should be the result of the following command::
            snmpwalk -OnQ -c <community> -v <version> <hostname> .1
        @param filename: the path to the file containing the SNMP walk
        @type  filename: C{str}
        """
        if not os.path.exists(filename):
            raise DiscoveratorError("%s: No such file" % filename)
        walk = open(filename)
        for line in walk:
            if line.count("=") != 1:
                continue
            lineparts = line.strip().split(" = ")
            if len(lineparts) == 1:
                lineparts.append("")
            self.oids[ lineparts[0] ] = lineparts[1]
        # Find the hostname using SNMPv2-MIB::sysName.0
        self.hostname = self.oids[".1.3.6.1.2.1.1.5.0"]

    def scanhost(self, host, community="public", version="2c"):
        """
        Get a full SNMP walk on the host using the snmpwalk system command.
        @param host: the host name
        @type  host: C{str}
        @param community: the SNMP community
        @type  community: C{str}
        @param version: the SNMP version
        @type  version: C{str}
        """
        self.hostname = host
        if community != "public":
            self.attributes["community"] = community
        if version != "2c":
            self.attributes["snmpVersion"] = version
        snmpcommand = ["snmpwalk", "-OnQ", "-c", community,
                       "-v", version, host, ".1"]
        newenv = os.environ.copy()
        newenv["LANG"] = "C"
        walkprocess = subprocess.Popen(snmpcommand,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       env=newenv)
        pout, perr = walkprocess.communicate()
        if walkprocess.returncode != 0:
            message = "SNMP walk command failed with error status %s " \
                      % walkprocess.returncode \
                     +"and message:\n%s\n" % perr \
                     +"The command was: %s" % " ".join(snmpcommand)
            raise DiscoveratorError(message)
        for line in pout.split("\n"):
            if line.count("=") != 1:
                continue
            oid, value = line.strip().split(" = ")
            self.oids[oid] = value

    def detect(self):
        """Start the detection on this host"""
        self.find_tests()
        self.find_attributes()
        self.find_hclasses()

    def find_tests(self):
        """Find the applicable tests using the test's detect() function"""
        for test in conf.testfactory.get_tests():
            # Was it already detected ?
            if test.__name__ in [ t["name"] for t in self.tests ]:
                continue
            detected = test().detect(self.oids)
            if detected:
                if detected is True:
                    self.tests.append({"class": test,
                                       "name": test.__name__,
                                      })
                elif isinstance(detected, list):
                    for arglist in detected:
                        self.tests.append({"class": test,
                                           "name": test.__name__,
                                           "args": arglist,
                                          })

    def find_hclasses(self):
        """Get the host classes"""
        self.find_hclasses_from_tests()
        self.find_hclasses_sysdescr()
        self.find_hclasses_oid()
        self.find_hclasses_function()

    def find_hclasses_from_tests(self):
        """Get the host classes from the detected tests"""
        for testdict in self.tests:
            test_hclass = conf.testfactory.get_hclass(testdict["class"])
            if test_hclass:
                self.hclasses.add(test_hclass)

    def find_hclasses_sysdescr(self):
        """Get the host classes from the sysDescr matching"""
        for hclass in conf.testfactory.get_hclasses():
            if not conf.testfactory.hclasschecks.has_key(hclass):
                continue
            sysdescrre = conf.testfactory.hclasschecks[hclass]["sysdescr"]
            if sysdescrre is None:
                continue
            if re.match(sysdescrre, self.oids[".1.3.6.1.2.1.1.1.0"]):
                self.hclasses.add(hclass)

    def find_hclasses_oid(self):
        """Get the host classes by testing the OID presence"""
        for hclass in conf.testfactory.get_hclasses():
            if not conf.testfactory.hclasschecks.has_key(hclass):
                continue
            oid = conf.testfactory.hclasschecks[hclass]["oid"]
            if oid is None:
                continue
            if oid in self.oids.keys():
                self.hclasses.add(hclass)

    def find_hclasses_function(self):
        """Get the host classes from a hardcoded mapping"""
        for hclass in conf.testfactory.get_hclasses():
            if not conf.testfactory.hclasschecks.has_key(hclass):
                continue
            detect_snmp = conf.testfactory.hclasschecks[hclass]["detect_snmp"]
            if detect_snmp is None:
                continue
            result = eval(detect_snmp)(self.oids)
            if result:
                self.hclasses.add(hclass)

    def find_attributes(self):
        """Find attributes about the host (number of CPUs, partitions, ...)"""
        # Use the custom hostname detection method
        self.find_attribute_hostname()
        # Detect using the tests' detect_attribute_snmp() method
        for testdict in self.tests:
            newattrs = testdict["class"]().detect_attribute_snmp(self.oids)
            if newattrs:
                self.attributes.update(newattrs)

    def find_attribute_hostname(self):
        """Find the hostname. If given an IP address, resolve the hostname"""
        if re.match(r"^\d+\.\d+\.\d+\.\d+$", self.hostname):
            self.ipaddr = self.hostname
            self.hostname = socket.gethostbyaddr(self.hostname)[0]
        if self.hostname.count(".") == 0:
            self.hostname = socket.getfqdn(self.hostname)
        if self.ipaddr is None:
            self.ipaddr = socket.gethostbyname(self.hostname)

    def declaration(self):
        """Generate the textual declaration for the ConfMgr"""
        self.hclasses.remove("all")
        decl = ["""h = Host("%s", "%s", "%s", classes=%s)""" \
                % (self.hostname, self.ipaddr, self.group,
                   str(list(self.hclasses))) ]
        for attr, val in self.attributes.iteritems():
            decl.append('h.add_attribute("%s", %s)' % (attr, str(val)))
        for testdict in self.tests:
            tmpdecl = 'h.add_test("%s"' % testdict["name"]
            if testdict.has_key("args"):
                for arg, val in testdict["args"].iteritems():
                    tmpdecl += ', %s="%s"' % (arg, val)
            tmpdecl += ")"
            decl.append(tmpdecl)
        return "\n".join(decl)



def main():
    """Start the discoverator"""
    conf.loadConf()
    # command-line arguments parsing
    parser = OptionParser()
    # declare all options
    parser.add_option("-f", "--file", dest="file",
                      help="Use FILE as the result of the SNMP walk")
    parser.add_option("-c", "--community", dest="community",
                      help="SNMP community")
    parser.add_option("-v", "--version", dest="version", help="SNMP version")
    parser.add_option("-H", "--host", dest="host", help="Host to scan")
    parser.add_option("-g", "--group", dest="group", default="Servers",
                      help="Default group")

    # parse the command line
    (options, args) = parser.parse_args()
    if not options.file and not options.host:
        parser.error("You must specify a host or a file")

    discoverator = Discoverator(options.group)

    # Handle command-line options
    if options.file:
        discoverator.scanfile(options.file)
    else:
        if not options.host:
            parser.error("You must specify a host or a file")
        if not options.community:
            options.community = "public"
        if not options.version:
            options.version = "2c"
        discoverator.scanhost(options.host,
                              options.community,
                              options.version)
    discoverator.detect()
    print(discoverator.declaration())


if __name__ == "__main__":
    main()
