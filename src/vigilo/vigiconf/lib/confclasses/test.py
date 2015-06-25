# -*- coding: utf-8 -*-
################################################################################
#
# Copyright (C) 2007-2015 CS-SI
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
import imp
import inspect
import sys

from pkg_resources import working_set

from vigilo.vigiconf.lib.exceptions import ParsingError
from vigilo.common.logging import get_logger, get_error_message
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

class Test(object):
    """
    A generic test class. All tests inherit from this class.

    @cvar oids: A list of SNMP OIDs which are specific to this host class
    @type oids: C{list}
    """

    oids = []
    __test__ = False # pour Nose

    def __init__(self, host, directives):
        """
        Initialise le test de supervision.

        @param host: L'hôte auquel le test de supervision est rattaché.
        @type  host: L{Host<lib.confclasses.host.Host>}
        @param directives: Directives Nagios à appliquer.
        @type directives: C{dict}
        """
        self.host = host
        self.directives = directives

    def _inject_defaults(self, kwargs):
        """
        Injecte les valeurs par défaut de certains attributs
        dans les paramètres d'une méthode de manipulation des
        services de l'hôte.

        @param kwargs: Les paramètres nommés passés à la méthode
            de manipulation des services.
        @type kwargs: C{dict}
        """
        kwargs.setdefault('directives', self.directives)

    def add_collector_service(self, *args, **kwargs):
        self._inject_defaults(kwargs)
        self.host.add_collector_service(*args, **kwargs)

    def add_collector_metro(self, *args, **kwargs):
        self.host.add_collector_metro(*args, **kwargs)

    def add_collector_service_and_metro(self, *args, **kwargs):
        self._inject_defaults(kwargs)
        self.host.add_collector_service_and_metro(*args, **kwargs)

    def add_collector_service_and_metro_and_graph(self, *args, **kwargs):
        self._inject_defaults(kwargs)
        self.host.add_collector_service_and_metro_and_graph(*args, **kwargs)

    def add_graph(self, *args, **kwargs):
        self.host.add_graph(*args, **kwargs)

    def add_external_sup_service(self, *args, **kwargs):
        self._inject_defaults(kwargs)
        self.host.add_external_sup_service(*args, **kwargs)

    def add_custom_service(self, *args, **kwargs):
        self._inject_defaults(kwargs)
        self.host.add_custom_service(*args, **kwargs)

    def add_perfdata(self, *args, **kwargs):
        self.host.add_perfdata(*args, **kwargs)

    def add_perfdata_handler(self, *args, **kwargs):
        self.host.add_perfdata_handler(*args, **kwargs)

    def add_metro_service(self, *args, **kwargs):
        self._inject_defaults(kwargs)
        self.host.add_metro_service(*args, **kwargs)

    def add_telnet_service(self, *args, **kwargs):
        self._inject_defaults(kwargs)
        self.host.add_telnet_service(*args, **kwargs)

    def add_trap(self, *args, **kwargs):
        self.host.add_trap(*args, **kwargs)

    def add_netflow(self, *args, **kwargs):
        self.host.add_netflow(*args, **kwargs)

    def _get_inc_graph_prefix(self, prefix):
        """
        Génère un préfixe de nom de graphe incrémental
        à partir d'un préfixe statique.

        @param prefix: Préfixe statique du nom du graphe.
        @type prefix: C{str}
        @return: Préfixe de nom de graphe incrémenté.
        @rtype: C{str}
        """
        graph_prefix = prefix
        current_graphs = self.host.hosts[self.host.name]["graphItems"].keys()
        i = 1
        while True:
            # Si l'un des graphes actuels contient déjà ce préfixe,
            # alors on va en générer un nouveau.
            for title in current_graphs:
                if title.startswith(graph_prefix):
                    break
            # Sinon, le préfixe actuel peut être utilisé librement.
            else:
                break
            i += 1
            graph_prefix = "%s (%d)" % (prefix, i)
        return graph_prefix


    @classmethod
    def as_bool(cls, value):
        """
        Convertit la valeur donnée en booléen.

        Les chaînes de caractères '1', 'true', 'on' et 'yes'
        sont évaluées comme valant C{True}, tandis que les chaînes
        '0', 'false', 'off' et 'no' sont évaluées comme valant
        C{False}.

        Si la valeur donnée est déjà un booléen, elle est
        retournée sans modification.

        @param value: Valeur à convertir.
        @type value: C{bool} or C{str}
        @return: Booléen obtenu après la conversion.
        @rtype: C{bool}
        """
        # S'il s'agissait déjà d'un booléen, on ne fait rien.
        if isinstance(value, bool):
            return value

        value = value.lower()
        if value in ('1', 'true', 'on', 'yes'):
            return True
        elif value in ('0', 'false', 'off', 'no'):
            return False
        raise ParsingError('A boolean was expected')


    @classmethod
    def as_int(cls, value):
        """
        Convertit la valeur donnée en nombre entier.

        Si la valeur donnée est déjà un entier, elle est
        retournée sans modification.

        @param value: Valeur à convertir.
        @type value: C{int} or C{str}
        @return: Nombre entier obtenu après la conversion.
        @rtype: C{int}
        """
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ParsingError('An integer was expected')


    @classmethod
    def as_float(cls, value):
        """
        Convertit la valeur donnée en flottant.

        Si la valeur donnée est déjà un flottant, elle est
        retournée sans modification.

        @param value: Valeur à convertir.
        @type value: C{float} or C{str}
        @return: Nombre flottant obtenu après la conversion.
        @rtype: C{float}
        """
        try:
            return float(value)
        except (TypeError, ValueError):
            raise ParsingError('A floating point value was expected')


    def add_test(self):
        """
        Add the test to the host provided as 1st argument.
        @note: This method must be implemented by subclasses.
        """
        pass

    @classmethod
    def detect(cls, walk):
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
        if hasattr(cls, "detect_snmp"):
            return getattr(cls, "detect_snmp")(walk)
        return cls.detect_oid(walk)

    @classmethod
    def detect_oid(cls, walk):
        """
        Use the walk OID hashmap to detect if this test is applicable.

        A test is applicable if one of the OIDs in the class variable "oid" is
        found in the OID hashmap's keys.

        @param walk: the SNMP walk to check against
        @type  walk: C{dict}
        @rtype: bool
        """
        if not cls.oids:
            return False
        for cur_oid in walk.keys():
            for test_oid in cls.oids:
                if cur_oid == test_oid or cur_oid.startswith(test_oid + "."):
                    return True
        return False

    @classmethod
    def detect_attribute_snmp(cls, walk):
        """
        Use the walk OID hashmap to detect attributes for the host where
        the walk comes from. Those attributes can then be used in the
        add_test() method.

        @param walk: the SNMP walk to check against
        @type  walk: C{dict}
        @return: A dictionary mapping attributes to their values.
        @rtype: C{dict}
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

    __test__ = False # pour Nose

    def __init__(self, confdir):
        self.tests = {}
        self.hclasschecks = {}
        self.path = self._list_test_paths(confdir)
        if not self.tests:
            self.load_tests()

    def _list_test_paths(self, confdir):
        paths = []
        for entry in working_set.iter_entry_points(
                        "vigilo.vigiconf.testlib"):
            path = entry.load().__path__[0]
            if not os.path.isdir(path):
                LOGGER.warning(_("Invalid entry point %(epname)s in package "
                                 "%(eppkg)s: %(epmodname)s") %
                               {"epname": entry.name,
                                "eppkg": entry.dist,
                                "epmodname": entry.module_name,
                               })
                continue
            paths.append(path)
        paths.append(os.path.join(confdir, "tests"))
        return paths

    def _filter_tests(self, obj):
        """
        Retourne C{True} si l'objet passé en argument est une classe Python
        décrivant un test de supervision ou C{False} dans le cas contraire.
        """
        return type(obj) == type(Test) and \
                issubclass(obj, Test) and \
                obj != Test

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

                # On charge d'abord la classe d'équipements.
                try:
                    mod_info = imp.find_module(hclass, [pathdir])
                except ImportError:
                    LOGGER.warning(
                        _('Invalid hostclass "%s". Missing __init__.py?') %
                        hclass
                    )
                    continue
                try:
                    mod = imp.load_module(
                            "vigilo.vigiconf.tests.%s" % hclass,
                            *mod_info)
                except KeyboardInterrupt:
                    raise
                except Exception, e:
                    LOGGER.warning(
                        _("Unable to load %(file)s: %(error)s") % {
                            'file': hclassdir,
                            'error': get_error_message(e),
                         })
                    continue

                # Puis les tests qu'elle contient.
                testfiles = set()
                for testfile in os.listdir(hclassdir):
                    if (not testfile.endswith((".py", ".pyc", ".pyo"))) or \
                            testfile.startswith("__"):
                        continue
                    mod_name = testfile.rpartition('.')[0]
                    # Évite de charger plusieurs fois le même test
                    # (depuis le .py et depuis le .pyc par exemple).
                    if mod_name in testfiles:
                        continue
                    # Load the file and get the class name
                    try:
                        mod_info = imp.find_module(mod_name, [hclassdir])
                    except ImportError:
                        # On ignore silencieusement l'erreur.
                        continue

                    try:
                        mod = imp.load_module(
                            "vigilo.vigiconf.tests.%s.%s" % (hclass, mod_name),
                            *mod_info)
                    except KeyboardInterrupt:
                        raise
                    except Exception, e:
                        raise
                        LOGGER.warning(
                            _("Unable to load %(file)s: %(error)s") % {
                                'file': os.path.join(hclassdir, testfile),
                                'error': get_error_message(e),
                             })
                    else:
                        for current_test_name, current_test_class \
                            in inspect.getmembers(mod, self._filter_tests):
                            if not self.tests.has_key(current_test_name):
                                self.tests[current_test_name] = {}
                            self.tests[current_test_name][hclass] = \
                                current_test_class
                        testfiles.add(mod_name)
                    finally:
                        # find_module() ouvre un descripteur de fichier
                        # en cas de succès et c'est à nous de le refermer.
                        if mod_info[0]:
                            mod_info[0].close()

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

    def get_hclasses(self):
        """
        Get the host classes where tests are using the provided oids.
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
         - the second technique is an attribute named "oids": if one of the OIDs
           in the attribute "oids" is found in the OIDS hashmap's keys, then the
           host class applies to it.
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
                self.hclasschecks[hclass] = {
                    "sysdescr": None,
                    "oids": None,
                    "detect_snmp": None,
                }

                try:
                    mod_info = imp.find_module(hclass, [pathdir])
                except ImportError:
                    # Pas de fichier __init__.py, __init__.pyc
                    # ou __init__.pyo.
                    continue

                try:
                    mod = imp.load_module(
                            "vigilo.vigiconf.tests.%s" % hclass,
                            *mod_info)
                except KeyboardInterrupt:
                    raise
                except Exception, e:
                    LOGGER.warning(
                        _("Unable to load %(file)s: %(error)s") % {
                            'file': hclassdir,
                            'error': get_error_message(e),
                         })
                else:
                    # Mise à jour des prédicats en fonction du contenu
                    # du fichier __init__ du module.
                    for hccheck in self.hclasschecks[hclass].keys():
                        if hasattr(mod, hccheck):
                            self.hclasschecks[hclass][hccheck] = \
                                getattr(mod, hccheck)
                finally:
                    # find_module() ouvre un descripteur de fichier
                    # en cas de succès et c'est à nous de le refermer.
                    if mod_info[0]:
                        mod_info[0].close()
