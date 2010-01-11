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
This module contains the classes needed to handle the tests
"""

from __future__ import absolute_import

import os
import sys

from vigilo.common.conf import settings


class Test(object):
    """
    A generic test class. All tests inherit from this class.

    @cvar oids: A list of SNMP OIDs which are specific to this host class
    @type oids: C{list}
    """

    oids = []

    def add_test(self, host):
        """
        Add the test to the host provided as 1st argument. 
        @note: This method must be implemented by subclasses.
        @type  host: L{Host<lib.confclasses.host.Host>}
        @param host: The host to add the test to
        """
        pass

    def detect(self, walk):
        """
        Use the walk OID hashmap to detect if this test is applicable.
        There are two ways to test this:
         - by declaring a list of OIDs in the oids instance variable
         - by defining a detect_snmp method, which will do more complex tests
           on the provided SNMP walk.

        If the detect_snmp() method is defined, it takes precedence over the
        OID list.
        The detect_snmp() method must return a list of dicts, where the dicts
        contain the arguments for the add_test() method. Example::

            [ { "cntrlid": 0,
                "logvolid": 1,
              },
              { "cntrlid": 0,
                "logvolid": 2,
              },
            ]

        If the add_test() method requires no argument, just return True.

        @param walk: the SNMP walk to check against
        @type  walk: C{dict}
        """
        if hasattr(self, "detect_snmp"):
            return getattr(self, "detect_snmp")(walk)
        return self.detect_oid(walk)

    def detect_oid(self, walk):
        """
        Use the walk OID hashmap to detect if this test is applicable.

        A test is applicable if one of the OIDs in the class variable "oid" is
        found in the OID hashmap's keys.

        @param walk: the SNMP walk to check against
        @type  walk: C{dict}
        @rtype: bool
        """
        if not self.oids:
            return False
        for cur_oid in walk.keys():
            for test_oid in self.oids:
                if cur_oid.startswith(test_oid):
                    return True
        return False

    def detect_attribute_snmp(self, walk):
        """
        Use the walk OID hashmap to detect attributes for the host where
        the walk comes from. Those attributes can then be used in the
        add_test() method.

        @param walk: the SNMP walk to check against
        @type  walk: C{dict}
        @rtype: dict of attributes to values.
        """
        pass


class TestFactory(object):
    """
    Handle our test library
    @cvar tests: the test library
    @type tests: C{dict}. See the L{load_tests}() method for details
    @cvar hclasschecks: the list of host class check methods
    @type hclasschecks: C{dict}. See the L{load_hclasses_checks} method for
        details
    @ivar path: the paths to look for tests
    @type path: C{list}
    """

    tests = {}
    hclasschecks = {}

    def __init__(self):
        self.path = [ 
                  os.path.join(
                      os.path.dirname(__file__), "..", "..", "tests"),
                  os.path.join(
                      settings.get("CONFDIR", "/etc/vigilo-vigiconf/conf.d"),
                      "tests"),
                    ]
        if not self.tests:
            self.load_tests()

    def load_tests(self):
        """
        Get all the available tests.

        It sets the self.tests class attributes as a dict reflecting the path
        to get a test. Example::
         
            { "Test1": { "hclass1": <class Test1 from hclass1/Test1.py>,
                         "hclass2": <class Test1 from hclass2/Test1.py>,
                         "hclass3": <class Test1 from hclass3/Test1.py>,
                       },
              "Test2": { "hclass1": <class Test2 from hclass1/Test2.py>,
                         "hclass4": <class Test2 from hclass4/Test2.py>,
                       },
            }
        """
        for pathdir in self.path:
            if not os.path.exists(pathdir):
                continue
            for hclass in os.listdir(pathdir):
                if hclass.startswith("."):
                    continue
                hclassdir = os.path.join(pathdir, hclass)
                if not os.path.isdir(hclassdir):
                    continue
                for testfile in os.listdir(hclassdir):
                    if not testfile.endswith(".py") or \
                            testfile.startswith("__"):
                        continue
                    # Load the file and get the class name
                    temp_locals = {}
                    execfile(os.path.join(hclassdir, testfile),
                             globals(), temp_locals)
                    for current_test_name, current_test_class \
                            in temp_locals.iteritems():
                        if current_test_name in sys.modules:
                            # This is an import statement, re-bind it here
                            globals()[current_test_name] = current_test_class
                            continue
                        if not issubclass(current_test_class, Test):
                            continue
                        if not self.tests.has_key(current_test_name):
                            self.tests[current_test_name] = {}
                        self.tests[current_test_name]\
                                             [hclass] = current_test_class

    def get_testnames(self, hclasses=None):
        """
        Get the names of the available tests, optionnaly for a list of host
        classes.
        @param hclasses: host classes to filter against
        @type  hclasses: C{list}
        @rtype: C{set}
        """
        tests_list = set()
        for test in self.get_tests(hclasses=hclasses):
            tests_list.add(test.__name__)
        return tests_list


    def get_test(self, test_name=None, hclasses=None):
        """
        Get a list of classes implementing a test on various host classes.
        Can be filtered either by test name or by host class.
        @param test_name: test name to filter against
        @type  test_name: C{str}
        @param hclasses: host classes to filter against
        @type  hclasses: C{list}
        @rtype: C{list}
        """
        test_list = []
        for current_test_name in self.tests:
            if test_name is not None and test_name != current_test_name:
                continue
            for hclass in self.tests[current_test_name]:
                if hclasses is not None and hclass not in hclasses:
                    continue
                test_list.append(self.tests[current_test_name][hclass])
        return test_list


#    def add_test(self, host, test_name, **kw):
#        """
#        Adds a test to a host, with the optionnal kw arguments
#        @param host: the host to add to
#        @type  host: L{Server<lib.server.Server>}
#        @param test_name: the name of the test to add
#        @type  test_name: C{str}
#        @param kw: the test arguments
#        @type  kw: C{dict}
#        """
#        test_list = self.get_test(test_name, host.classes)
#        for test_class in test_list:
#            test_class().add_test(host, **kw)

    def get_hclasses(self):
        """
        Get the host classes where tests are using the provided oid.
        @rtype: C{set}
        """
        hclasses = set()
        for hcs in self.tests.values():
            hclasses.update(set(hcs.keys()))
        return hclasses

    def get_tests(self, hclasses=None):
        """
        Get the available tests, optionally filtering by host class.
        @param hclasses: host classes to filter against
        @type  hclasses: C{list}
        @rtype: C{set}
        """
        tests = set()
        for test_name in self.tests:
            for hclass, testclass in self.tests[test_name].iteritems():
                if hclasses and hclass not in hclasses:
                    continue
                # no hclass selected: return all
                tests.add(testclass)
        return tests

    def get_hclass(self, testclass):
        """
        Get the host class of a test class.
        @param testclass: the test class to get the host class from
        @type  testclass: L{Test}
        """
        for test_name in self.tests:
            for hclass, curtestclass in self.tests[test_name].iteritems():
                if testclass is curtestclass:
                    return hclass

    def load_hclasses_checks(self):
        """
        Get all the available methods to check for a host class validity.

        Each host class can define in a __init__.py file three techniques to
        check if a host corresponds to the host class.
         - the first technique is an attribute named "sysdescr": a regexp which
           will be matched against the SNMPv2-MIB::sysDescr.0
           (.1.3.6.1.2.1.1.1.0) result. Be careful to include leading and
           ending wildcards (.*) as needed.
         - the second technique is an attribute named "oid": if this OID is
           present in a host's SNMP walk, then the host class applies to it.
         - the third technique is a detect_snmp() function, for more complex
           matching.  This function is given the whole SNMP result map, and
           returns True or False if the host class applies to this result.

        This method loads these techniques in the L{hclasschecks} hashmap for
        each available host class.

        This function is mainly used by the
        L{Discoverator<discoverator.Discoverator>}.
        """
        if self.hclasschecks:
            return # already loaded
        for pathdir in self.path:
            if not os.path.exists(pathdir):
                continue
            for hclass in os.listdir(pathdir):
                if hclass.startswith("."):
                    continue
                hclassdir = os.path.join(pathdir, hclass)
                if not os.path.isdir(hclassdir):
                    continue
                initfile = os.path.join(hclassdir,"__init__.py")
                if not os.path.exists(initfile):
                    continue
                # Load the file and get the attribute and the function
                temp_locals = {}
                execfile(os.path.join(hclassdir, "__init__.py"),
                         globals(), temp_locals)
                #from pprint import pprint; pprint(temp_locals)
                hccheck = {"sysdescr": None, "oid": None, "detect_snmp": None}
                hccheck.update(temp_locals)
                del hccheck["__doc__"] # small cleanup
                self.hclasschecks[hclass] = hccheck

