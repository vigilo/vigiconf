# -*- coding: utf-8 -*-
################################################################################
#
# Copyright (C) 2007-2013 CS-SI
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
import subprocess
import re
import socket
from xml.etree import ElementTree as ET # Python 2.5
#from pprint import pprint

from . import conf
from .lib import VigiConfError

from vigilo.common.gettext import translate
_ = translate(__name__)

class DiscoveratorError(VigiConfError):
    """Error during the Discoverator process"""
    pass
class SnmpwalkNotInstalled(DiscoveratorError):
    """The snmpwalk command is not installed"""
    pass

class Discoverator(object):
    """
    Scan a host or file containing the hosts' SNMP walk to find the host
    classes and the available tests.
    Also extract information about the host (number of CPUs, etc...)
    """

    def __init__(self, testfactory, group=None):
        self.group = group
        self.oids = {}
        self.hclasses = set()
        self.tests = []
        self.hostname = None
        self.ipaddr = None
        self.attributes = {}
        self.testfactory = testfactory
        self.testfactory.load_hclasses_checks()

    def _get_snmp_command(self, community, version, host):
        """
        @return: La commande système à utiliser pour scanner un hôte
        @rtype: C{list}
        """
        return ["snmpwalk", "-OnQe", "-c", community, "-v", version, host, ".1"]

    def scan(self, target, community="public", version="2c"):
        if community != "public":
            self.attributes["snmpCommunity"] = community
        if version != "2c":
            self.attributes["snmpVersion"] = version
        if os.path.exists(target):
            self.scanfile(target)
        else:
            self.scanhost(target, community, version)

    def read_output(self, iterator):
        """
        Lis la sortie du snmpwalk (en direct ou par fichier) en re-fusionnant
        les lignes contenant un retour à la ligne
        """
        line_re = re.compile("^((?:\.\d+)+) =\s?(.*)$")
        cur_oid = None
        full_value = False
        need_quote = False
        cur_value = ""

        for line in iterator:
            line_mo = line_re.match(line)
            if line_mo is not None:
                # Cas d'une valeur multiligne sans guillemets.
                if cur_value and not need_quote:
                    self._add_OID_value(cur_oid, cur_value)

                cur_oid = line_mo.group(1)
                cur_value = line_mo.group(2).strip("\n\r")

                # Cas d'une valeur entre guillemets.
                if cur_value.startswith('"'):
                    # La valeur se termine sur la ligne où elle a commencé.
                    if cur_value.endswith('"'):
                        need_quote = False
                    else:
                        need_quote = True

            # Continuation de la valeur d'une ligne précédente.
            else:
                cur_value = cur_value + "\n" + line.rstrip("\r\n")
                # Si la ligne se termine par un guillemet,
                # alors la valeur est terminée.
                if need_quote and cur_value.endswith('"'):
                    need_quote = False
                    self._add_OID_value(cur_oid, cur_value)

        # Cas de la dernière valeur.
        # cur_oid vaut None lorsque le fichier est vide.
        if cur_oid and cur_value:
            self._add_OID_value(cur_oid, cur_value)

    _hexcheck_re = re.compile("^(?:[0-9a-f]{2} \r?\n?)+00 $", re.I)
    _hex_re = re.compile("(?:([0-9a-f]{2}) \r?\n?)", re.I)

    def _unhex(self, s):
        return s.group(1).decode('hex')

    def _add_OID_value(self, cur_oid, cur_value):
        # Depuis net-snmp 5.4.0, les chaînes de caractères
        # sont délimitées par des guillemets dans le walk.
        if cur_value.startswith('"') and \
            cur_value.endswith('"') and \
            len(cur_value) >= 2:
            cur_value = cur_value[1:-1]

            # Conversion des chaînes hexadécimales
            # et suppression du '\x00' terminal.
            if self._hexcheck_re.match(cur_value):
                cur_value = self._hex_re.sub(self._unhex, cur_value)[:-1]
        self.oids[cur_oid] = cur_value

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
        self.read_output(walk)
        # Find the hostname using SNMPv2-MIB::sysName.0
        if ".1.3.6.1.2.1.1.5.0" not in self.oids:
            raise DiscoveratorError(_("Can't find the hostname using "
                                      "SNMPv2-MIB::sysName.0"))
        self.hostname = self.oids[".1.3.6.1.2.1.1.5.0"].strip()
        if re.search('\s', self.hostname):
            raise DiscoveratorError(_("Invalid HOSTNAME detected in "
                    "SNMPv2-MIB::sysName.0: \"%s\" (blank character "
                    "not allowed)") % self.hostname)

    def scanhost(self, host, community, version):
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
        snmpcommand = self._get_snmp_command(community, version, host)
        newenv = os.environ.copy()
        newenv["LANGUAGE"] = "C"
        newenv["LANG"] = "C"
        newenv["LC_ALL"] = "C"
        #SNMPCONFPATH=/dev/null permit to avoid unwanted setup from
        #    - /etc/snmp/snmp.local.conf
        #    - /etc/snmp/snmp.conf
        newenv["SNMPCONFPATH"] = "/dev/null"
        walkprocess = subprocess.Popen(snmpcommand,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       env=newenv)
        out, err = walkprocess.communicate()
        if walkprocess.returncode == 127:
            message = _('The "snmpwalk" command is not installed.')
            raise SnmpwalkNotInstalled(message)
        self.read_output(out.split("\n")) # pylint: disable-msg=E1103
        if walkprocess.returncode != 0:
            message = _("SNMP walk command failed with error status %(status)s "
                        "and message:\n  %(msg)s\nThe command was: %(cmd)s") % {
                'status': walkprocess.returncode,
                'msg': err.strip(), # pylint: disable-msg=E1103
                'cmd': " ".join(snmpcommand),
            }
            raise DiscoveratorError(message)

    def detect(self, tests=None):
        """
        Start the detection on this host
        @param tests: list des tests spécifiques (None si tous les tests
            doivent être détectés)
        @type  tests: C{list}
        """
        self.find_tests(tests)
        self.find_attributes()
        self.find_hclasses()
        self.deduplicate_tests()

    def find_tests(self, tests=None):
        """
        Find the applicable tests using the test's detect() function
        @param tests: Liste des tests spécifiques (None si tous les tests
            doivent être détectés).
        @type  tests: C{list} of C{str}
        """
        for test in self.testfactory.get_tests():
            # is it one of the tests "specifically wanted" to be detected ?
            if tests and test.__name__ not in tests:
                continue
            detected = test.detect(self.oids)
            if detected:
                if detected is True:
                    self.tests.append({"class": test,
                                       "name": test.__name__,
                                       "args": {},
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
            test_hclass = self.testfactory.get_hclass(testdict["class"])
            if test_hclass:
                self.hclasses.add(test_hclass)

    def find_hclasses_sysdescr(self):
        """Get the host classes from the sysDescr matching"""
        for hclass in self.testfactory.get_hclasses():
            if not self.testfactory.hclasschecks.has_key(hclass):
                continue
            sysdescrre = self.testfactory.hclasschecks[hclass]["sysdescr"]
            if sysdescrre is None or ".1.3.6.1.2.1.1.1.0" not in self.oids:
                continue
            if re.match(sysdescrre, self.oids[".1.3.6.1.2.1.1.1.0"], re.S):
                self.hclasses.add(hclass)

    def find_hclasses_oid(self):
        """Get the host classes by testing the OID presence"""
        for hclass in self.testfactory.get_hclasses():
            if not self.testfactory.hclasschecks.has_key(hclass):
                continue
            oid = self.testfactory.hclasschecks[hclass]["oid"]
            if oid is None:
                continue
            if oid in self.oids.keys():
                self.hclasses.add(hclass)

    def find_hclasses_function(self):
        """Get the host classes from a hardcoded mapping"""
        for hclass in self.testfactory.get_hclasses():
            if not self.testfactory.hclasschecks.has_key(hclass):
                continue
            detect_snmp = self.testfactory.hclasschecks[hclass]["detect_snmp"]
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
            newattrs = testdict["class"].detect_attribute_snmp(self.oids)
            if newattrs:
                self.attributes.update(newattrs)

    def find_attribute_hostname(self):
        """Find the hostname. If given an IP address, resolve the hostname"""
        if re.match(r"^\d+\.\d+\.\d+\.\d+$", self.hostname):
            self.ipaddr = self.hostname
            try:
                self.hostname = socket.gethostbyaddr(self.hostname)[0]
            except socket.error:
                pass
        if self.hostname.count(".") == 0:
            self.hostname = socket.getfqdn(self.hostname)
        if self.ipaddr is None:
            try:
                self.ipaddr = socket.gethostbyname(self.hostname)
            except socket.error:
                pass

    def deduplicate_tests(self):
        new_tests = []
        seen = []
        for testdict in self.tests:
            if (testdict["name"], testdict["args"]) in seen:
                continue # doublon
            new_tests.append(testdict)
            seen.append((testdict["name"], testdict["args"]))
        self.tests = new_tests

    def declaration(self):
        """Generate the textual declaration for Vigiconf"""
        if "all" in self.hclasses:
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
                    if item:
                        _attr_item = ET.SubElement(_attr, "item")
                        _attr_item.text = item
            else:
                _attr.text = val
        for testdict in self.tests:
            _test = ET.SubElement(decl, "test")
            _test.set("name", testdict["name"])
            for arg, val in testdict["args"].iteritems():
                _arg = ET.SubElement(_test, "arg")
                _arg.set("name", arg)
                _arg.text = val
        #tree = ET.ElementTree(decl)
        return decl


def indent(elem, level=0):
    """ indentation function.

    @param elem: element
    @type  elem: L{ET}
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
