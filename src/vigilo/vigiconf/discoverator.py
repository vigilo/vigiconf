# -*- coding: utf-8 -*-
# Copyright (C) 2007-2020 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
This module contains the Discoverator, a tool to generate the supervision
configuation of a host by analysing its SNMP MIB.
"""

from __future__ import absolute_import

import os
import subprocess
import re
import socket
import inspect
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

def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    if isinstance(s, list):
        return s
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(_nsre, s)]


class DisplayNameRetriever(object):
    """
    Mock the behaviour of vigilo.vigiconf.lib.confclasses.host.Host,
    to intercept calls to methods that add new collector services.
    This is used to retrieve a potential display name for the tests.
    """
    # This attribute is used during the tests when a validation error occurs.
    name = None

    def __init__(self, testname):
        self.names = []
        self.testname = testname

    def add_collector_service(self, label, *args, **kw):
        self.names.append("%s (%s)" % (label, self.testname))

    def add_collector_metro(self, *args, **kw):
        pass

    def add_graph(self, *args, **kw):
        pass

    def get_names(self):
        """Retrieve candidates display names."""
        return self.names


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
        @param tests: Liste des tests spécifiques (None si tous les tests
            doivent être détectés)
        @type  tests: C{list}
        """
        self.find_tests(tests, self.find_hclasses())
        self.find_attributes()
        self.deduplicate_tests()

    def _build_test_conf(self, cls, args):
        """
        Build the configuration for some detected test,
        including a suggested display name.
        """
        name = cls.get_fullname()
        dummy = DisplayNameRetriever(name)
        display = []
        try:
            cls(dummy, {}).add_test(**dict(args))
            display.extend(dummy.get_names())
        except TypeError:
            pass

        display.append(name)
        return {
            "class": cls,
            "name": name,
            "args": args,
            "display_name": display[0],
        }


    def find_tests(self, tests=None, hclasses=None):
        """
        Find the applicable tests using the test's detect() function
        @param tests: Liste des tests spécifiques (None si tous les tests
            doivent être détectés).
        @type  tests: C{list} of C{str}
        """
        for test in self.testfactory.get_tests(hclasses):
            # is it one of the tests "specifically wanted" to be detected ?
            if tests and test.__name__ not in tests:
                continue

            detected = test.detect(self.oids)
            if detected:
                if detected is True:
                    self.tests.append(self._build_test_conf(test, []))
                elif isinstance(detected, list):
                    for arglist in detected:
                        self.tests.append(self._build_test_conf(
                            test, sorted(arglist.items())))


    def find_hclasses(self):
        hclasses  = self.find_hclasses_sysdescr()
        hclasses &= self.find_hclasses_oids()
        hclasses &= self.find_hclasses_function()
        return hclasses

    def find_hclasses_sysdescr(self):
        """Get the host classes from the sysDescr matching"""
        hclasses = set()
        for hclass in self.testfactory.get_hclasses():
            checks = self.testfactory.hclasschecks.get(hclass, {})
            sysdescrre = checks.get("sysdescr")
            if sysdescrre is None or ".1.3.6.1.2.1.1.1.0" not in self.oids:
                hclasses.add(hclass)
            elif re.match(sysdescrre, self.oids[".1.3.6.1.2.1.1.1.0"], re.S):
                hclasses.add(hclass)
        return hclasses

    def _find_oids(self, oids):
        """Return True if one of the oids match"""
        for cur_oid in self.oids.keys():
            for test_oid in oids:
                if cur_oid.startswith(test_oid):
                    return True
        return False

    def find_hclasses_oids(self):
        """Get the host classes by testing the OID presence"""
        hclasses = set()
        for hclass in self.testfactory.get_hclasses():
            oids = self.testfactory.hclasschecks.get(hclass, {}).get("oids")
            if not oids:
                hclasses.add(hclass)
            elif self._find_oids(oids):
                hclasses.add(hclass)
        return hclasses

    def find_hclasses_function(self):
        """Get the host classes using a detection function"""
        hclasses = set()
        for hclass in self.testfactory.get_hclasses():
            checks = self.testfactory.hclasschecks.get(hclass, {})
            detect_snmp = checks.get("detect_snmp")
            if detect_snmp is None:
                hclasses.add(hclass)
            elif detect_snmp(self.oids):
                hclasses.add(hclass)
        return hclasses

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
        """
        Cette méthode élimine les doublons dans les définitions des tests.
        Elle élimine également les tests qui sont des parents d'autres tests.
        """
        new_tests = []
        seen_tests = []
        seen_classes = set()

        # Trie les tests selon la profondeur de leur hiérarchie de classes
        # (de la plus longue à la plus courte), pour traiter d'abord les
        # descendants, puis leurs parents, etc. en remontant.
        self.tests.sort(key=lambda x: len(inspect.getmro(x["class"])),
                        reverse=True)
        for testdict in self.tests:
            key = (testdict["name"], testdict["args"])
            if key in seen_tests:
                continue # doublon du test (même classe, nom et arguments)

            if repr(testdict["class"]) in seen_classes:
                continue # un test héritant de cette classe est déjà présent

            new_tests.append(testdict)
            seen_tests.append(key)
            seen_classes |= set( repr(cls) for cls
                                 in inspect.getmro(testdict["class"])[1:] )

        # Trie les tests :
        # - par leur nom en premier lieu
        # - par la valeur de leurs arguments ensuite
        #
        # Le tri se fait selon l'ordre naturel (plus pertinent pour les
        # interfaces réseau par exemple) plutôt que purement alphabétique.
        self.tests = sorted(new_tests, key=lambda test: (
                natural_sort_key(test['name']),
                [natural_sort_key(val) for arg, val in test['args']]
            ))

    def declaration(self):
        """Generate the textual declaration for Vigiconf"""
        decl = ET.Element("host")
        decl.set("name", self.hostname)
        if self.ipaddr is not None:
            decl.set("address", self.ipaddr)
        group = ET.SubElement(decl, "group")
        group.text = self.group
        for attr, val in self.attributes.iteritems():
            _attr = ET.SubElement(decl, "attribute")
            _attr.set("name", attr)
            _attr.set("xml:space", "preserve")
            if isinstance(val, list):
                for item in val:
                    if item:
                        _attr_item = ET.SubElement(_attr, "item")
                        _attr_item.text = item
            else:
                _attr.text = val
        for testdict in self.tests:
            decl.append(ET.Comment(testdict["display_name"]))
            _test = ET.SubElement(decl, "test")
            _test.set("name", testdict["name"])
            for arg, val in testdict["args"]:
                _arg = ET.SubElement(_test, "arg")
                _arg.set("name", arg)
                if isinstance(val, list):
                    for item in val:
                        if item:
                            _arg_item = ET.SubElement(_arg, "item")
                            _arg_item.text = item
                            _arg_item.set("xml:space", "preserve")
                else:
                    _arg.text = val
                    _arg.set("xml:space", "preserve")
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
