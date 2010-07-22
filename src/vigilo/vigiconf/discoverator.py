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

from __future__ import absolute_import

import os
import sys
import subprocess
import re
import socket
from optparse import OptionParser
from xml.etree import ElementTree as ET # Python 2.5
#from pprint import pprint

from . import conf
from .lib import VigiConfError

from vigilo.common.gettext import translate
_ = translate(__name__)

class DiscoveratorError(VigiConfError):
    """Error during the Discoverator process"""
    pass

class Discoverator(object):
    """
    Scan a host or file containing the hosts' SNMP walk to find the host
    classes and the available tests.
    Also extract information about the host (number of CPUs, etc...)
    @ivar snmpcommand: The system command to scan a host
    @type snmpcommand: C{str}
    """

    snmpcommand = "snmpwalk -OnQe -c %(community)s -v %(version)s" \
                 +" \"%(host)s\" .1"

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
            SNMPCONFPATH=/dev/null snmpwalk -OnQe -c <community> -v <version> <hostname> .1
        SNMPCONFPATH=/dev/null permit to avoid unwanted setup from
            - /etc/snmp/snmp.local.conf
            - /etc/snmp/snmp.conf  
        @param filename: the path to the file containing the SNMP walk
        @type  filename: C{str}
        """
        if not os.path.exists(filename):
            raise DiscoveratorError(_("%s: No such file") % filename)
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
        snmpcommand = self.snmpcommand % {"community": community,
                                          "version": version,
                                          "host": host,
                                         }
        newenv = os.environ.copy()
        newenv["LANG"] = "C"
        newenv["LC_ALL"] = "C"
        #SNMPCONFPATH=/dev/null permit to avoid unwanted setup from 
        #    - /etc/snmp/snmp.local.conf
        #    - /etc/snmp/snmp.conf
        newenv["SNMPCONFPATH"] = "/dev/null"
        walkprocess = subprocess.Popen(snmpcommand,
                                       shell=True,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       env=newenv)
        pout, perr = walkprocess.communicate()
        if walkprocess.returncode == 127:
            message = _('The "snmpwalk" command is not installed.')
            raise DiscoveratorError(message)
        elif walkprocess.returncode != 0:
            message = _("SNMP walk command failed with error status %(status)s "
                        "and message:\n%(msg)s\nThe command was: %(cmd)s") % {
                'status': walkprocess.returncode,
                'msg': perr,
                'cmd': snmpcommand,
            }
            raise DiscoveratorError(message)
        for line in pout.split("\n"): # pylint: disable-msg=E1103
            if line.count("=") != 1:
                continue
            linetuple = line.strip().split(" = ")
            if len(linetuple) != 2:
                continue
            oid, value = linetuple
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
            try:
                self.ipaddr = socket.gethostbyname(self.hostname)
            except socket.gaierror:
                pass

    def declaration(self):
        """Generate the textual declaration for Vigiconf"""
        self.hclasses.remove("all")
        decl = ET.Element("host")
        decl.set("name", self.hostname)
        if self.ipaddr is not None:
            decl.set("address", self.ipaddr)
        group = ET.SubElement(decl, "group")
        group.text = self.group
        for hclass in self.hclasses:
            _class = ET.SubElement(decl, "class")
            _class.text = hclass
        for attr, val in self.attributes.iteritems():
            _attr = ET.SubElement(decl, "attribute")
            _attr.set("name", attr)
            if isinstance(val, list):
                for item in val:
                    _attr_item = ET.SubElement(_attr, "item")
                    _attr_item.text = item
            else:
                _attr.text = val
        for testdict in self.tests:
            _test = ET.SubElement(decl, "test")
            _test.set("name", testdict["name"])
            if testdict.has_key("args"):
                for arg, val in testdict["args"].iteritems():
                    _arg = ET.SubElement(_test, "arg")
                    _arg.set("name", arg)
                    _arg.text = val
        #tree = ET.ElementTree(decl)
        return decl


def indent(elem, level=0):
    """ indentation function.
    
    @param elem: element
    @type  elem: L{Element}
    @param level: indentation level
    @type  level: C{int}
    """
    i = "\n" + level*"    "
    if len(elem):
        # pylint: disable-msg=W0631
        if not elem.text or not elem.text.strip():
            elem.text = i + "    "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


if __name__ == "__main__":
    main()
