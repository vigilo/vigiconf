# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# pylint: disable-msg=C0111,W0212,R0904
# Copyright (C) 2006-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>


import os
import re
import vigilo.vigiconf.conf as conf
from vigilo.vigiconf.lib.confclasses.host import Host
from vigilo.vigiconf.applications.nagios import Nagios
from vigilo.models.demo.functions import add_host, add_dependency_group, \
                                         add_dependency
from vigilo.models.tables import ConfFile
from helpers import GeneratorBaseTestCase


class NagiosGeneratorTestCase(GeneratorBaseTestCase):

    def _get_apps(self):
        return {"nagios": Nagios()}

    def test_basic(self):
        """Nagios: fonctionnement nominal"""
        test_list = self.testfactory.get_test("Interface", self.host.classes)
        self.host.add_tests(test_list, {"label":"eth0", "ifname":"eth0"})
        self._generate()
        nagiosconf = os.path.join(self.basedir, "localhost",
                                  "nagios", "nagios.cfg")
        self.assert_(os.path.exists(nagiosconf),
                     "Nagios conf file was not generated")
        self._validate()

    def test_unicode(self):
        """Nagios: caractères unicode"""
        test_list = self.testfactory.get_test("Interface", self.host.classes)
        self.host.add_tests(test_list, {"label":u"aàeéècç",
                                        "ifname":u"aàeéècç"})
        self._generate()
        nagiosconf = os.path.join(self.basedir, "localhost",
                                  "nagios", "nagios.cfg")
        self.assert_(os.path.exists(nagiosconf),
                     "Nagios conf file was not generated")
        self._validate()

    def test_add_metro_service(self):
        """Nagios: add_metro_service"""
        test_list = self.testfactory.get_test("Interface", self.host.classes)
        self.host.add_tests(test_list, {"label":"eth1", "ifname":"eth1"})
        self.host.add_metro_service("Traffic in eth1", "ineth1", 10, 20)
        self._generate()
        nagiosconf = os.path.join(self.basedir, "localhost",
                                  "nagios", "nagios.cfg")
        self.assert_(os.path.exists(nagiosconf),
                     "Nagios conf file was not generated")
        nagios = open(nagiosconf).read()

        regexp_coll = re.compile(r"""
            define\s+service\s*\{\s*                # Inside an service definition
                use\s+generic-active-service\s*
                host_name\s+testserver1\s*
                service_description\s+Collector\s*
                check_command\s+Collector\s*
                max_check_attempts\s+2\s*
                [^\}]+                              # Any following declaration
                \}                                  # End of the host definition
            """,
            re.MULTILINE | re.VERBOSE)

        regexp_svc = re.compile(r"""
            define\s+service\s*\{\s*                # Inside an service definition
                use\s+generic-passive-service\s*
                host_name\s+testserver1\s*          # Working on the testserver1 host
                service_description\s+Traffic[ ]in[ ]eth1\s*
                \}                                  # End of the host definition
            """,
            re.MULTILINE | re.VERBOSE)
        print nagios
        self.assert_(regexp_coll.search(nagios) is not None,
            "add_metro_service does not generate proper nagios conf "
            "(Collector service)")
        self.assert_(regexp_svc.search(nagios) is not None,
            "add_metro_service does not generate proper nagios conf "
            "(passive service)")

    def test_force_passive(self):
        """Nagios: influence de l'attribut force-passive"""
        self.host.set_attribute("force-passive", True)
        self.host.add_external_sup_service("testservice", command="/bin/true")

        self._generate()
        nagiosconffile = os.path.join(self.basedir, "localhost",
                                      "nagios", "nagios.cfg")
        nagiosconf = open(nagiosconffile).read()
        print nagiosconf

        self.assertTrue(re.search("^\s*use\s+generic-passive-service\s*$",
                                  nagiosconf, re.M))

    def test_passive_host(self):
        """Nagios: génération d'un hôte passif"""
        self.host.set_attribute("hostTPL", "generic-passive-host")

        self._generate()
        nagiosconffile = os.path.join(self.basedir, "localhost",
                                      "nagios", "nagios.cfg")
        nagiosconf = open(nagiosconffile).read()
        print nagiosconf

        self.assertTrue(re.search("^\s*use\s+generic-passive-host\s*$",
                                  nagiosconf, re.M))

    def test_nagios_host_directives(self):
        """Nagios: host directives"""
        self.host.add_nagios_directive("max_check_attempts", "5")
        self.host.add_nagios_directive("check_interval", "10")
        self.host.add_nagios_directive("retry_interval", "1")

        self._generate()
        nagiosconffile = os.path.join(self.basedir, "localhost",
                                      "nagios", "nagios.cfg")
        self.assert_(os.path.exists(nagiosconffile),
                     "Nagios conf file was not generated")
        nagiosconf = open(nagiosconffile).read()
        print nagiosconf

        self.assertTrue("max_check_attempts      5" in nagiosconf)
        self.assertTrue("check_interval          10" in nagiosconf)
        self.assertTrue("retry_interval          1" in nagiosconf)

    def test_nagios_services_directives(self):
        """Nagios: host directives"""
        self.host.add_nagios_directive("obsess_over_service", "1", target="services")
        test_list = self.testfactory.get_test("Interface", self.host.classes)
        self.host.add_tests(test_list, {"label":"eth0", "ifname":"eth0"},)
        self._generate()
        nagiosconffile = os.path.join(self.basedir, "localhost",
                                      "nagios", "nagios.cfg")
        self.assert_(os.path.exists(nagiosconffile),
                     "Nagios conf file was not generated")
        nagiosconf = open(nagiosconffile).read()
        print nagiosconf

        self.assertTrue("obsess_over_service     1" in nagiosconf)

    def test_nagios_service_directives_collector(self):
        """Nagios: service directives"""
        test_list = self.testfactory.get_test("Interface", self.host.classes)
        self.host.add_tests(test_list, {"label":"eth0", "ifname":"eth0"},
                            directives={"testdirective": "testdirvalue"})
        self._generate()
        nagiosconffile = os.path.join(self.basedir, "localhost",
                                      "nagios", "nagios.cfg")
        self.assert_(os.path.exists(nagiosconffile),
                     "Nagios conf file was not generated")
        nagiosconf = open(nagiosconffile).read()
        print nagiosconf
        self.assertTrue("testdirective           testdirvalue" in nagiosconf)

    def test_nagios_service_directives_external(self):
        """Nagios: service directives"""
        self.host.add_external_sup_service("testservice",
                directives={"testdirective": "testdirvalue"})
        self._generate()
        nagiosconffile = os.path.join(self.basedir, "localhost",
                                      "nagios", "nagios.cfg")
        self.assert_(os.path.exists(nagiosconffile),
                     "Nagios conf file was not generated")
        nagiosconf = open(nagiosconffile).read()
        print nagiosconf
        self.assertTrue("testdirective           testdirvalue" in nagiosconf)

    def test_parents_directive(self):
        """Nagios: parents"""
        # On ajoute un 2ème hôte et on génère une dépendance topologique
        # de "testserver1" sur "testserver2".
        Host(conf.hostsConf, "host/localhost.xml", u"testserver2",
                     "192.168.1.2", "Servers")
        add_host("testserver2", ConfFile.get_or_create("dummy.xml"))
        dep_group = add_dependency_group('testserver1', None, 'topology')
        add_dependency(dep_group, ("testserver2", None))
        # "testserver2" doit apparaître comme parent de "testserver1"
        # dans le fichier de configuration généré pour Nagios.
        self._generate()
        nagiosconffile = os.path.join(self.basedir, "localhost",
                                      "nagios", "nagios.cfg")
        self.assert_(os.path.exists(nagiosconffile),
                     "Nagios conf file was not generated")
        nagiosconf = open(nagiosconffile).read()
        print nagiosconf
        self.assertTrue(re.search("^\s*parents\s+testserver2\s*$",
                        nagiosconf, re.M))
