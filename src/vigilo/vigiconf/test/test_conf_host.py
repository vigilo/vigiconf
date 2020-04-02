# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# pylint: disable-msg=C0111,W0212,R0904
# Copyright (C) 2006-2020 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>
from __future__ import absolute_import, print_function

import os
import unittest
import shutil

from vigilo.common.conf import settings

import vigilo.vigiconf.conf as conf
from vigilo.vigiconf.lib.confclasses.host import Host
from vigilo.vigiconf.lib.confclasses.hosttemplate import HostTemplate
from vigilo.vigiconf.lib.confclasses.hosttemplate import HostTemplateFactory
from vigilo.vigiconf.lib.confclasses.host import HostFactory
from vigilo.vigiconf.lib.confclasses.test import TestFactory
from vigilo.vigiconf.lib.confclasses.graph import Graph, Cdef
from vigilo.vigiconf.lib.exceptions import ParsingError, VigiConfError

from .helpers import setup_db, teardown_db, setup_tmpdir, TESTDATADIR

class HostMethods(unittest.TestCase):

    def setUp(self):
        conf.load_general_conf() # Réinitialisation de la configuration
        setup_db()
        self.testfactory = TestFactory(confdir=settings["vigiconf"]["confdir"])

        self.host = Host(conf.hostsConf, "dummy", u"testserver1",
                         u"192.168.1.1", u"Servers")
        self.expected = {
            "metrosrv": {
                "type": "passive",
                "directives": {},
                "reRoutedBy": None,
            },
        }

    def tearDown(self):
        teardown_db()

    def test_add_metro_service(self):
        """Test for the add_metro_service host method"""
        test_list = self.testfactory.get_test("all.Interface")
        self.host.add_tests(test_list, {"label":"eth1", "ifname":"eth1"})
        self.host.add_metro_service("Traffic in eth1", "ineth1", 10, 20)
        self.assertEqual(
            conf.hostsConf["testserver1"]["services"]["Traffic in eth1"],
            self.expected["metrosrv"])
        self.assert_('ineth1' in conf.hostsConf["testserver1"]["metro_services"])
        self.assertEqual(
            conf.hostsConf["testserver1"]["metro_services"]['ineth1'],
            {
                'servicename': 'Traffic in eth1',
                'warning': 10,
                'critical': 20,
                'factor': 1.0,
            }
        )

    def test_priority_host_hosttemplate(self):
        """Test priorite du parametrage des hosts sur les hosttemplates"""
        test_list = self.testfactory.get_test("all.Interface")
        self.host.add_tests(test_list, {"label":"eth0", "ifname":"eth0"})
        self.host.add_metro_service("Traffic in eth0", "ineth0", 10, 20)
        self.assertEqual(
            conf.hostsConf["testserver1"]["services"]["Traffic in eth0"],
            self.expected["metrosrv"])

    def test_add_metro_service_INTF(self):
        """Test for the add_metro_service function in the Interface test"""
        test_list = self.testfactory.get_test("all.Interface")
        self.host.add_tests(test_list, {"label":"eth0", "ifname":"eth0",
                                        "warn": ("10", "20"),
                                        "crit": ("30", "40")})
        self.assertEqual(
            conf.hostsConf["testserver1"]["services"]["Traffic in eth0"],
            self.expected["metrosrv"])
        self.assert_('ineth0' in conf.hostsConf["testserver1"]["metro_services"])
        self.assertEqual(
            conf.hostsConf["testserver1"]["metro_services"]['ineth0'],
            {
                'servicename': 'Traffic in eth0',
                'warning': 10,
                'critical': 30,
                'factor': 8,
            }
        )

        self.assertEqual(
            conf.hostsConf["testserver1"]["services"]["Traffic out eth0"],
            self.expected["metrosrv"])
        self.assert_('outeth0' in conf.hostsConf["testserver1"]["metro_services"])
        self.assertEqual(
            conf.hostsConf["testserver1"]["metro_services"]['outeth0'],
            {
                'servicename': 'Traffic out eth0',
                'warning': 20,
                'critical': 40,
                'factor': 8,
            }
        )

    def test_invalid_INTF_admin_value(self):
        """Valeurs autorisées pour le paramètre 'admin' du test Interface."""
        test_list = self.testfactory.get_test("all.Interface")

        # Les valeurs i/w/c doivent être acceptées.
        for value in ('i', 'w', 'c'):
            self.host.add_tests(test_list, {"label":"eth0", "ifname":"eth0",
                                            "admin": value})
            self.assertEqual(
                conf.hostsConf["testserver1"]["SNMPJobs"]\
                    [ ("Interface eth0", "service") ]['params'],
                # 'c' correspond à la valeur par défaut de "dormant".
                ['eth0', 'eth0', value, 'c', 'c'])

        # Les autres valeurs doivent être rejetées.
        self.assertRaises(ParsingError, self.host.add_tests,
            test_list, {"label":"eth0", "ifname":"eth0", "admin": ''})

    def test_invalid_INTF_dormant_value(self):
        """Valeurs autorisées pour le paramètre 'dormant' du test Interface."""
        test_list = self.testfactory.get_test("all.Interface")

        # Les valeurs i/w/c doivent être acceptées.
        for value in ('i', 'w', 'c'):
            self.host.add_tests(test_list, {"label":"eth0", "ifname":"eth0",
                                            "dormant": value})
            self.assertEqual(
                conf.hostsConf["testserver1"]["SNMPJobs"]\
                    [ ("Interface eth0", "service") ]['params'],
                # 'i' correspond à la valeur par défaut de "admin".
                ['eth0', 'eth0', 'i', value, 'c'])

        # Les autres valeurs doivent être rejetées.
        self.assertRaises(ParsingError, self.host.add_tests,
            test_list, {"label":"eth0", "ifname":"eth0", "dormant": ''})

    def test_invalid_INTF_alarmondown_value(self):
        """Valeurs autorisées pour le paramètre 'alarmondown' du test Interface."""
        test_list = self.testfactory.get_test("all.Interface")

        # Les valeurs i/w/c doivent être acceptées.
        for value in ('i', 'w', 'c'):
            self.host.add_tests(test_list, {"label":"eth0", "ifname":"eth0",
                                            "alarmondown": value})
            self.assertEqual(
                conf.hostsConf["testserver1"]["SNMPJobs"]\
                    [ ("Interface eth0", "service") ]['params'],
                # 'i' correspond à la valeur par défaut de "admin".
                ['eth0', 'eth0', 'i', 'c', value])

        # Les autres valeurs doivent être rejetées.
        self.assertRaises(ParsingError, self.host.add_tests,
            test_list, {"label":"eth0", "ifname":"eth0", "alarmondown": ''})

    def test_add_tag_hosts(self):
        """Test for the add_tag method on hosts"""
        self.host.add_tag("Host", "important", 2)
        self.assertEqual(conf.hostsConf["testserver1"]["tags"],
                         {"important": 2})

    def test_add_tag_services(self):
        """Test for the add_tag method on services"""
        test_list = self.testfactory.get_test("all.UpTime")
        self.host.add_tests(test_list)
        self.host.add_tag("UpTime", "security", 1)
        self.assertEqual({"security": 1},
                conf.hostsConf["testserver1"]["services"]["UpTime"]["tags"])

    def test_add_trap(self):
        """Test for the add_trap method on hosts"""
        self.host.add_trap(".1.2.3", "CRITICAL", None, None, [])
        expected = {
            None: [
                (".1.2.3", "CRITICAL", None, []),
            ],
        }
        self.assertEqual(expected, conf.hostsConf["testserver1"]["snmpTrap"])

    def test_add_group(self):
        """Test for the add_group method on hosts"""
        self.host.add_group("/Test Group")
        self.assertTrue("/Test Group" in
                conf.hostsConf["testserver1"]["otherGroups"],
                "add_group does not work")

    def test_add_collector_service(self):
        """Test for the add_collector_service method on hosts"""
        self.host.add_collector_service(
            "TestAddCS",
            "TestAddCSFunction",
            ["fake arg 1"],
            ["GET/.1.3.6.1.2.1.1.3.0"]
        )
        hostdata = conf.hostsConf["testserver1"]
        self.assertEqual(hostdata["services"]["TestAddCS"]["type"],
                "passive", "add_collector_service does not fill the "
                "services sub-hashmap")
        self.assertEqual(hostdata["SNMPJobs"][("TestAddCS", "service")],
                { 'function': "TestAddCSFunction",
                  'params': ["fake arg 1"],
                  'vars': ["GET/.1.3.6.1.2.1.1.3.0"],
                  'reRouteFor': None },
                "add_collector_service does not fill the SNMPJobs sub-hashmap")

    def test_add_collector_service_reroute(self):
        """Test for the add_collector_service host method with rerouting"""
        host2 = Host(conf.hostsConf, "dummy", "testserver2", "192.168.1.2", "Servers")
        host2.add_collector_service(
            "TestAddCSReRoute",
            "TestAddCSReRouteFunction",
            ["fake arg 1"],
            ["GET/.1.3.6.1.2.1.1.3.0"],
            reroutefor={
                'host': "testserver1",
                "service": "TestAddCSReRoute",
            },
        )
        hdata1 = conf.hostsConf["testserver1"]
        hdata2 = conf.hostsConf["testserver2"]
        self.assertEqual(hdata1["services"]["TestAddCSReRoute"]["type"],
            "passive", "add_collector_service rerouting does not work "
            "with the services sub-hashmap")
        self.assertEqual(hdata2["SNMPJobs"][("TestAddCSReRoute", "service")],
                { 'function': "TestAddCSReRouteFunction",
                  'params': ["fake arg 1"],
                  'vars': ["GET/.1.3.6.1.2.1.1.3.0"],
                  'reRouteFor': {
                    'host': "testserver1",
                    "service": "TestAddCSReRoute"
                  },
                }, "add_collector_service rerouting does not work "
                "with the SNMPJobs sub-hashmap")

    def test_add_collector_metro(self):
        """Test for the add_collector_metro host method"""
        self.host.add_collector_metro("TestAddCS", "TestAddCSMFunction",
                            ["fake arg 1"], ["GET/.1.3.6.1.2.1.1.3.0"],
                            "GAUGE", label="TestAddCSLabel")
        self.assertEqual(
            conf.hostsConf["testserver1"]["dataSources"]["TestAddCS"],
            {'dsType':"GAUGE", 'label': "TestAddCSLabel",
             "max": None, "min": None, "rra_template": None},
            "add_collector_metro does not fill the dataSources sub-hashmap")
        self.assertEqual(
            conf.hostsConf["testserver1"]["SNMPJobs"][("TestAddCS","perfData")],
            {'function': "TestAddCSMFunction", 'params': ["fake arg 1"],
             'vars': ["GET/.1.3.6.1.2.1.1.3.0"], 'reRouteFor': None},
            "add_collector_metro does not fill the SNMPJobs sub-hashmap")

    def test_add_collector_metro_reroute(self):
        """Test for the add_collector_metro host method with rerouting"""
        host2 = Host(conf.hostsConf, "dummy", u"testserver2",
                     u"192.168.1.2", "Servers")
        host2.add_collector_metro("TestAddCSReRoute", "TestAddCSRRMFunction",
                ["fake arg 1"], ["GET/.1.3.6.1.2.1.1.3.0"],
                "GAUGE", label="TestAddCSReRouteLabel",
                reroutefor={'host': "testserver1",
                            "service": "TestAddCSReRoute"} )
        t1ds = conf.hostsConf["testserver1"]["dataSources"]
        t2snmp = conf.hostsConf["testserver2"]["SNMPJobs"]
        self.assertEqual(t1ds["TestAddCSReRoute"],
            {'dsType':"GAUGE", 'label': "TestAddCSReRouteLabel",
             "max": None, "min": None, "rra_template": None},
            "add_collector_metro rerouting does not work with the "
            "dataSources sub-hashmap")
        self.assertEqual(t2snmp[("TestAddCSReRoute","perfData")],
            {'function': "TestAddCSRRMFunction", 'params': ["fake arg 1"],
             'vars': ["GET/.1.3.6.1.2.1.1.3.0"], 'reRouteFor':
             {'host':"testserver1", "service" : "TestAddCSReRoute"}},
            "add_collector_service ReRouting does not work with the "
            "SNMPJobs sub-hashmap")

    def test_add_nagios_hdirective(self):
        """Test for the add_nagios_directive method"""
        host = Host(conf.hostsConf, "dummy", u"testserver2",
                    u"192.168.1.2", "Servers")
        host.add_nagios_directive("max_check_attempts", "5")
        nagios_hdirs = conf.hostsConf["testserver2"]["nagiosDirectives"]["host"]
        self.assertEqual(nagios_hdirs["max_check_attempts"], "5")

    def test_add_nagios_sdirective(self):
        """Test for the add_nagios_directive method"""
        host = Host(conf.hostsConf, "dummy", u"test2",
                    u"192.168.1.2", "Servers")
        host.add_nagios_directive("max_check_attempts", "5", target="services")
        nagios_sdirs = conf.hostsConf["test2"]["nagiosDirectives"]["services"]
        self.assertEqual(nagios_sdirs["max_check_attempts"], "5")

    def test_add_nagios_service_directive_INTF(self):
        """Nagios directives for tests"""
        test_list = self.testfactory.get_test("all.Interface")
        self.host.add_tests(test_list, {"label":"eth0", "ifname":"eth0"},
                            directives={"testdirective": "testdirvalue"})
        nsd = conf.hostsConf["testserver1"]["nagiosSrvDirs"]
        self.assertEqual(nsd["Interface eth0"]["testdirective"],
                          "testdirvalue")

    def test_add_graph(self):
        self.host.add(self.host.name, "dataSources", "dummyds", {})
        graph = self.host.add_graph("testgraph", ["dummyds"], "lines", "test")
        self.assertTrue("testgraph" in
                        conf.hostsConf["testserver1"]["graphItems"])

    def test_make_cdef(self):
        cdef = self.host.make_rrd_cdef("testcdef", "1,1,+")
        self.assertTrue("testcdef" in
                        conf.hostsConf["testserver1"]["dataSources"])
        graph = self.host.add_graph("testgraph", [cdef], "lines", "test")
        print(conf.hostsConf["testserver1"]["graphItems"]["testgraph"]["cdefs"])
        self.assertEqual(
            conf.hostsConf["testserver1"]["graphItems"]["testgraph"]["cdefs"],
            [{"name": "testcdef", "cdef": "1,1,+"}])

    def test_make_cdef_unicode(self):
        self.assertRaises(VigiConfError, self.host.make_rrd_cdef,
                          u"test éèçà", "1,1,+")

    def test_make_cdef_8bit(self):
        self.assertRaises(VigiConfError, self.host.make_rrd_cdef,
                          "test éèçà", "1,1,+")

    def test_host_redefinition(self):
        """Tentative de re-définition d'un hôte"""
        Host(conf.hostsConf, "dummy", u"twice",
             u"192.168.1.2", "Servers")

        # La détection des doublons se fait en utilisant le nom.
        # Pour s'en assurer, on fait varier l'adresse IP.
        self.assertRaises(VigiConfError, Host,
            conf.hostsConf, "dummy", u"twice",
            u"192.168.1.3", "Servers")


class HostFactoryMethods(unittest.TestCase):

    def setUp(self):
        conf.load_general_conf() # Réinitialisation de la configuration
        setup_db()
        self.tmpdir = setup_tmpdir()
        self.testfactory = TestFactory(confdir=self.tmpdir)
        self.hosttemplatefactory = HostTemplateFactory(self.testfactory)

    def tearDown(self):
        teardown_db()
        shutil.rmtree(self.tmpdir)


    def test_load(self):
        """Test of the loading of the conf test hosts"""
        xmlfile = open(os.path.join(self.tmpdir, "localhost.xml"), "w")
        xmlfile.write("""
            <host name="localhost" address="127.0.0.1">
                <group>Linux servers</group>
            </host>
        """)
        xmlfile.close()
        self.hosttemplatefactory.register(HostTemplate("default"))
        f = HostFactory(
                self.tmpdir,
                self.hosttemplatefactory,
                self.testfactory,
            )
        hosts = f.load()
        print(hosts)
        self.assertTrue(hosts.has_key('localhost'),
                        "localhost defined in conf")

    def test_load_with_nagios_directives(self):
        """Loading some host with nagios directives."""
        # ces templates sont utilisés dans les fichiers
        for tplname in ["default", "linux"]:
            htpl = HostTemplate(tplname)
            self.hosttemplatefactory.register(htpl)
        # sans ça le no_secondary_groups.xml va pas passer
        htpl.add_group("dummy_group")
        f = HostFactory(
                os.path.join(TESTDATADIR, "xsd/hosts/ok"),
                self.hosttemplatefactory,
                self.testfactory,
            )

        # validation par XSD
        hosts = f.load(validation=True)
        testserver = hosts['example-nagios-spec.xml']
        nagios_hdirs = testserver.get('nagiosDirectives')["host"]
        print(nagios_hdirs)
        self.assertEqual(nagios_hdirs['max_check_attempts'], "5")
        self.assertEqual(nagios_hdirs['check_interval'], "10")
        self.assertEqual(nagios_hdirs['retry_interval'], "1")

        nagios_sdirs = testserver.get('nagiosSrvDirs')
        print(nagios_sdirs)
        self.assertEqual(nagios_sdirs['Interface eth0']['max_check_attempts'],
                          "5")
        self.assertEqual(nagios_sdirs['Interface eth0']['check_interval'],
                          "10")
        self.assertEqual(nagios_sdirs['Interface eth0']['retry_interval'],
                          "1")

    def test_diamond_templates(self):
        """
        Attribut d'un hôte et héritage en diamant des templates (#921).

        Le template "default" définit la communauté SNMP à "public".
        Celle-ci est redéfinie dans "testtpl1" comme valant "not-public".
        Enfin, "testtpl2" est chargé après "testtpl1" et ne redéfinit
        PAS la communauté.

        Ce test vérifie que "testtpl2" n'écrase pas la communauté
        définie par "testtpl1" en chargeant à nouveau "default"
        (et donc, en réinitialisant la valeur à "public").
        """
        default = HostTemplate("default")
        default.add_attribute("snmpCommunity", u"public")
        self.hosttemplatefactory.register(default)

        tpl1 = HostTemplate("testtpl1")
        tpl1.add_attribute("snmpCommunity", u"not-public")
        self.hosttemplatefactory.register(tpl1)

        tpl2 = HostTemplate("testtpl2")
        self.hosttemplatefactory.register(tpl2)

        # Recharge les templates.
        self.hosttemplatefactory.load_templates()

        xmlfile = open(os.path.join(self.tmpdir, "localhost.xml"), "w")
        xmlfile.write("""
            <host name="localhost" address="127.0.0.1">
                <template>testtpl1</template>
                <template>testtpl2</template>
                <group>Linux servers</group>
            </host>
        """)
        xmlfile.close()

        f = HostFactory(
                self.tmpdir,
                self.hosttemplatefactory,
                self.testfactory,
            )

        hosts = f.load()
        print(hosts)
        # La communauté SNMP doit valoir "not-public"
        # (elle ne doit pas avoir été réinitialisée à "public").
        self.assertEqual(
            hosts['localhost'].get('snmpCommunity'),
            "not-public"
        )


class HostAndHosttemplatesInheritance(unittest.TestCase):
    """
    Vérifie le comportement de l'héritage d'informations depuis les
    modèles d'hôtes à destination des hôtes eux-mêmes.
    """

    def setUp(self):
        conf.load_general_conf() # Réinitialisation de la configuration
        setup_db()
        testfactory = TestFactory(confdir=settings["vigiconf"]["confdir"])
        self.tmpdir = setup_tmpdir()
        self.testfactory = TestFactory(confdir=self.tmpdir)
        self.hosttemplatefactory = HostTemplateFactory(self.testfactory)
        self.hosttemplatefactory.register(HostTemplate("default"))
        self.tpl = HostTemplate("testtpl1")
        self.hosttemplatefactory.register(self.tpl)
        conf.hostsConf = {}
        self.hostfactory = HostFactory(
            self.tmpdir,
            self.hosttemplatefactory,
            self.testfactory
        )

    def tearDown(self):
        teardown_db()
        shutil.rmtree(self.tmpdir)

    def test_inherit_test(self):
        """
        Héritage d'un test depuis un modèle d'hôte.

        Le template "testtpl1" ajoute le test "UpTime".
        Le template "testtpl2" hérite de "testtpl1".
        L'hôte "localhost" importe le template "testtpl2".
        Le test "UpTime" doit donc être appliqué à "localhost".
        """
        self.tpl.add_test("all.UpTime")
        tpl2 = HostTemplate("testtpl2")
        tpl2.add_parent("testtpl1")
        self.hosttemplatefactory.register(tpl2)
        # Reload the templates
        self.hosttemplatefactory.load_templates()

        xmlfile = open(os.path.join(self.tmpdir, "localhost.xml"), "w")
        xmlfile.write("""
            <host name="localhost" address="127.0.0.1">
                <template>testtpl2</template>
                <group>Linux servers</group>
            </host>
        """)
        xmlfile.close()
        hosts = self.hostfactory.load()
        print(hosts)
        self.assertTrue("UpTime" in hosts['localhost']['services'],
                        "inheritance does not work with tests")

    def test_inherit_group(self):
        """
        Héritage d'un groupe depuis un modèle d'hôte.

        Le template "testtpl1" s'ajoute au groupe "Test Group".
        Le template "testtpl2" hérite de "testtpl1".
        L'hôte "localhost" importe le template "testtpl2".
        L'hôte "localhost" devrait donc appartenir au groupe "Test Group".
        """
        self.tpl.add_group("Test Group")
        tpl2 = HostTemplate("testtpl2")
        tpl2.add_parent("testtpl1")
        self.hosttemplatefactory.register(tpl2)
        # Reload the templates
        self.hosttemplatefactory.load_templates()

        xmlfile = open(os.path.join(self.tmpdir, "localhost.xml"), "w")
        xmlfile.write("""
            <host name="localhost" address="127.0.0.1">
                <template>testtpl2</template>
            </host>
        """)
        xmlfile.close()
        hosts = self.hostfactory.load()
        print(hosts)
        self.assertTrue("Test Group" in
                hosts["localhost"]["otherGroups"],
                "inheritance does not work with groups")

    def test_inherit_attribute(self):
        """
        Héritage d'un attribut depuis un modèle d'hôte.

        Le template "testtpl1" ajoute l'attribut "TestAttr" valant "TestVal".
        Le template "testtpl2" hérite de "testtpl1".
        L'hôte "localhost" importe le template "testtpl2".
        L'hôte "localhost" devrait donc posséder cet attribut avec
        la valeur définie dans "testtpl1".
        """
        self.tpl.add_attribute("TestAttr", "TestVal")
        tpl2 = HostTemplate("testtpl2")
        tpl2.add_parent("testtpl1")
        self.hosttemplatefactory.register(tpl2)
        # Reload the templates
        self.hosttemplatefactory.load_templates()

        xmlfile = open(os.path.join(self.tmpdir, "localhost.xml"), "w")
        xmlfile.write("""
            <host name="localhost" address="127.0.0.1">
                <template>testtpl2</template>
                <group>Linux servers</group>
            </host>
        """)
        xmlfile.close()
        hosts = self.hostfactory.load()
        print(hosts)
        self.assertTrue(hosts['localhost'].has_key("TestAttr"),
                "inheritance does not work with attributes")
        self.assertEqual(hosts['localhost']["TestAttr"], "TestVal",
                "inheritance does not work with attributes")

    def test_inherit_redefine_attribute(self):
        """
        Héritage d'un attribut redéfini depuis un modèle d'hôte.

        Le template "testtpl1" ajoute l'attribut "TestAttr" valant "TestVal1".
        Le template "testtpl2" hérite de "testtpl1" et redéfinit "TestAttr"
        comme valant "TestVal2".
        L'hôte "localhost" importe le template "testtpl2".
        L'hôte "localhost" devrait donc posséder cet attribut avec
        la valeur définie dans "testtpl2".
        """
        self.tpl.add_attribute("TestAttr", "TestVal1")
        tpl2 = HostTemplate("testtpl2")
        tpl2.add_parent("testtpl1")
        self.tpl.add_attribute("TestAttr", "TestVal2")
        self.hosttemplatefactory.register(tpl2)
        # Reload the templates
        self.hosttemplatefactory.load_templates()

        xmlfile = open(os.path.join(self.tmpdir, "localhost.xml"), "w")
        xmlfile.write("""
            <host name="localhost" address="127.0.0.1">
                <template>testtpl2</template>
                <group>Linux servers</group>
            </host>
        """)
        xmlfile.close()
        hosts = self.hostfactory.load()
        print(hosts)
        self.assertTrue(hosts['localhost'].has_key("TestAttr"),
                "inheritance does not work with attributes")
        self.assertEqual(hosts['localhost']["TestAttr"], "TestVal2",
                "inheritance does not work with attributes")

    def test_inherit_multiple_test(self):
        """
        Héritage de tests issus de modèles d'hôtes multiples.

        L'hôte hérite d'un template qui hérite lui-même de deux templates
        définissant chacun 1 test. On s'assure que l'hôte hérite correctement
        des 2 tests.
        """
        self.tpl.add_test("all.Interface", {"ifname":"eth0", "label":"Label0"})
        tpl2 = HostTemplate("testtpl2")
        tpl2.add_test("all.Interface", {"ifname":"eth1", "label":"Label1"})
        self.hosttemplatefactory.register(tpl2)
        tpl3 = HostTemplate("testtpl3")
        tpl3.add_parent(["testtpl1", "testtpl2"])
        self.hosttemplatefactory.register(tpl3)
        # Reload the templates
        self.hosttemplatefactory.load_templates()

        xmlfile = open(os.path.join(self.tmpdir, "localhost.xml"), "w")
        xmlfile.write("""
            <host name="localhost" address="127.0.0.1">
                <template>testtpl3</template>
                <group>Linux servers</group>
            </host>
        """)
        xmlfile.close()
        hosts = self.hostfactory.load()
        print(hosts)

        for svc in ("Interface Label0", "Interface Label1"):
            self.assertTrue(svc in hosts['localhost']['services'],
                    "multiple inheritance does not work (%s)" % svc)
