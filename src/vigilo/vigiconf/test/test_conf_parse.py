# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# pylint: disable-msg=C0111,W0212,R0904
# Copyright (C) 2006-2018 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>
from __future__ import absolute_import, print_function

import os
import unittest
import shutil
import glob
import subprocess
import pprint

from vigilo.common.conf import settings
settings.load_module(__name__)

import vigilo.vigiconf.conf as conf
from vigilo.vigiconf.lib import ParsingError, VigiConfError
from vigilo.vigiconf.loaders.group import GroupLoader
from vigilo.vigiconf.loaders.host import ServiceLoader
from vigilo.vigiconf.lib.confclasses.test import TestFactory
from vigilo.vigiconf.lib.confclasses.hosttemplate import HostTemplate
from vigilo.vigiconf.lib.confclasses.hosttemplate import HostTemplateFactory
from vigilo.vigiconf.lib.confclasses.host import HostFactory
from vigilo.models.tables import ConfFile
from vigilo.models.demo.functions import add_host

from .helpers import setup_tmpdir, setup_db, teardown_db


class ValidateXSD(unittest.TestCase):

    def setUp(self):
        self.dtddir = os.path.join(conf.CODEDIR, "validation", "xsd")
        self.hdir = os.path.join(settings["vigiconf"].get("confdir"), "hosts")
        self.htdir = os.path.join(settings["vigiconf"].get("confdir"),
                        "hosttemplates")

    def test_host(self):
        """Validate the provided hosts against the XSD"""
        devnull = open("/dev/null", "w")
        hosts = glob.glob(os.path.join(self.hdir, "*.xml"))
        for host in hosts:
            valid = subprocess.call(["xmllint", "--noout", "--schema",
                        os.path.join(self.dtddir, "host.xsd"), host],
                        stdout=devnull, stderr=subprocess.STDOUT)
            self.assertEqual(valid, 0, "Validation of host \"%s\" failed"
                              % os.path.basename(host))
        devnull.close()

    def test_hosttemplate(self):
        """Validate the provided hosttemplatess against the XSD"""
        devnull = open("/dev/null", "w")
        hts = glob.glob(os.path.join(self.htdir, "*.xml"))
        for ht in hts:
            valid = subprocess.call(["xmllint", "--noout", "--schema",
                        os.path.join(self.dtddir, "hosttemplate.xsd"), ht],
                        stdout=devnull, stderr=subprocess.STDOUT)
            self.assertEqual(valid, 0, "Validation of hosttemplate \"%s\" "
                              "failed" % os.path.basename(ht))
        devnull.close()


class ParseHost(unittest.TestCase):

    def setUp(self):
        setup_db()
        self.tmpdir = setup_tmpdir()
        os.mkdir(os.path.join(self.tmpdir, "hosts"))
        self.old_conf_path = settings["vigiconf"]["confdir"]
        settings["vigiconf"]["confdir"] = self.tmpdir
        testfactory = TestFactory(confdir=self.tmpdir)
        self.hosttemplatefactory = HostTemplateFactory(testfactory)
        self.hosttemplatefactory.register(HostTemplate("default"))
        self.hostfactory = HostFactory(
                        os.path.join(self.tmpdir, "hosts"),
                        self.hosttemplatefactory,
                        testfactory,
                      )
        self.hostsConf = self.hostfactory.hosts
        self.host = open(os.path.join(self.tmpdir, "hosts", "host.xml"), "w")

    def tearDown(self):
        # This has been overwritten in setUp, reset it
        settings["vigiconf"]["confdir"] = self.old_conf_path
        shutil.rmtree(self.tmpdir)
        teardown_db()

    def test_host(self):
        """Test the parsing of a basic host declaration"""
        GroupLoader().load()
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
            <group>/Servers/Linux servers</group>
        </host>""")
        self.host.close()
        self.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts",
                                    "host.xml"))
        pprint.pprint(self.hostsConf)
        self.assert_(self.hostsConf.has_key("testserver1"),
                "host is not properly parsed")
        self.assert_(self.hostsConf["testserver1"]["name"] == "testserver1",
                "host name is not properly parsed")
        self.assert_(self.hostsConf["testserver1"]["address"] == "192.168.1.1",
                "host address is not properly parsed")
        self.assert_(self.hostsConf["testserver1"]["serverGroup"] == "Servers",
                "host main group is not properly parsed")

    def test_host_passive(self):
        """Parsing d'un hôte passif"""
        GroupLoader().load()
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
            <force-passive/>
            <group>/Servers/Linux servers</group>
        </host>""")
        self.host.close()
        self.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts",
                                    "host.xml"))
        pprint.pprint(self.hostsConf)
        self.assertTrue(self.hostsConf["testserver1"]["force-passive"],
                "L'attribut force-passive n'est pas correctement parsé")

    def test_template(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
            <template>linux</template>
        </host>""")
        self.host.close()
        htpl = HostTemplate("linux")
        htpl.add_group("Linux servers")
        self.hosttemplatefactory.register(htpl)
        self.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts",
                                    "host.xml"))
        pprint.pprint(self.hostsConf)
        self.assertTrue("Linux servers" in
                        self.hostsConf["testserver1"]["otherGroups"],
                        "The \"template\" tag is not properly parsed")

    def test_template_passive(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
            <force-passive/>
            <template>linux</template>
        </host>""")
        self.host.close()
        htpl = HostTemplate("linux")
        htpl.add_group("Linux servers")
        self.hosttemplatefactory.register(htpl)
        self.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts",
                                    "host.xml"))
        pprint.pprint(self.hostsConf)
        self.assertTrue(self.hostsConf["testserver1"]["force-passive"],
                "L'attribut force-passive n'est pas conservé après "
                "application d'un template")

    def test_attribute(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
            <attribute name="cpulist">2</attribute>
            <group>/Servers</group>
        </host>""")
        self.host.close()
        self.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts",
                                    "host.xml"))
        pprint.pprint(self.hostsConf)
        self.assert_(self.hostsConf["testserver1"].has_key("cpulist") and
                     self.hostsConf["testserver1"]["cpulist"] == "2",
                     "The \"attribute\" tag is not properly parsed")

    def test_tag_host(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
            <tag service="Host" name="important">2</tag>
            <group>/Servers</group>
        </host>""")
        self.host.close()
        self.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts",
                                    "host.xml"))
        pprint.pprint(self.hostsConf)
        self.assert_("tags" in self.hostsConf["testserver1"] and
               "important" in self.hostsConf["testserver1"]["tags"] and
                self.hostsConf["testserver1"]["tags"]["important"] == "2",
                "The \"tag\" tag for hosts is not properly parsed")

    def test_nagios_directive_host(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
            <nagios>
                <directive name="obsess_over_host">1</directive>
            </nagios>
            <test name="all.UpTime"/>
            <group>/Servers</group>
        </host>""")
        self.host.close()
        self.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts",
                                    "host.xml"))
        pprint.pprint(self.hostsConf)
        self.assert_("host" in self.hostsConf["testserver1"]["nagiosDirectives"] and
               "obsess_over_host" in self.hostsConf["testserver1"]["nagiosDirectives"]["host"] and
                self.hostsConf["testserver1"]["nagiosDirectives"]["host"]["obsess_over_host"] == "1",
                "The \"directive\" for hosts is not properly parsed")

    def test_nagios_directive_service(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
            <nagios>
                <directive target="services" name="obsess_over_service">1</directive>
            </nagios>
            <test name="all.UpTime"/>
            <group>/Servers</group>
        </host>""")
        self.host.close()
        self.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts",
                                    "host.xml"))
        pprint.pprint(self.hostsConf)
        self.assert_("host" in self.hostsConf["testserver1"]["nagiosDirectives"] and
               "obsess_over_service" in self.hostsConf["testserver1"]["nagiosDirectives"]["services"] and
                self.hostsConf["testserver1"]["nagiosDirectives"]["services"]["obsess_over_service"] == "1",
                "The \"directive\" for services is not properly parsed")

    def test_empty_nagios_directive(self):
        """Pas d'erreur en cas de directive Nagios vide (#1293)."""
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
            <nagios>
                <directive name="obsess_over_host"></directive>
            </nagios>
            <test name="all.UpTime"/>
            <group>/Servers</group>
        </host>""")
        self.host.close()
        self.assertRaises(ParsingError, self.hostfactory._loadhosts,
                          os.path.join(self.tmpdir, "hosts", "host.xml"))

    def test_tag_service(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
            <test name="all.UpTime"/>
            <tag service="UpTime" name="important">2</tag>
            <group>/Servers</group>
        </host>""")
        self.host.close()
        self.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts",
                                    "host.xml"))
        self.assertTrue("tags" in
                self.hostsConf["testserver1"]["services"]["UpTime"]
                and "important" in
                self.hostsConf["testserver1"]["services"]["UpTime"]["tags"]
                and self.hostsConf["testserver1"]["services"]
                ["UpTime"]["tags"]["important"] == "2",
               "The \"tag\" tag for services is not properly parsed")

    def test_group(self):
        GroupLoader().load()
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
            <group>Linux servers</group>
        </host>""")
        self.host.close()
        self.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts",
                                    "host.xml"))
        pprint.pprint(self.hostsConf)
        self.assertTrue("Linux servers" in
                self.hostsConf["testserver1"]["otherGroups"],
                "The \"group\" tag is not properly parsed")

    def test_group_multiple(self):
        GroupLoader().load()
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
            <group>Linux servers</group>
            <group>AIX servers</group>
        </host>""")
        self.host.close()
        self.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts",
                                    "host.xml"))
        pprint.pprint(self.hostsConf)
        self.assertTrue("Linux servers" in
                self.hostsConf["testserver1"]["otherGroups"]
                and "AIX servers" in
                self.hostsConf["testserver1"]["otherGroups"],
                "The \"group\" tag does not handle multiple values")

    def test_test(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
            <test name="all.Interface">
                <arg name="label">eth0</arg>
                <arg name="ifname">eth0</arg>
            </test>
            <group>/Servers</group>
        </host>""")
        self.host.close()
        self.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts",
                                    "host.xml"))
        pprint.pprint(self.hostsConf)
        self.assertTrue(('Interface eth0', 'service') in
                self.hostsConf["testserver1"]["SNMPJobs"],
                "The \"test\" tag is not properly parsed")

    def test_test_nonexistant(self):
        """
        Une exception doit être levée si on cherche à ajouter un test inexistant.
        """
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1">
            <test name="NonExistant"/>
            <group>/Servers</group>
        </host>""")
        self.host.close()
        filepath = os.path.join(self.tmpdir, "hosts", "host.xml")
        self.assertRaises(ParsingError, self.hostfactory._loadhosts, filepath)

    def test_ventilation_explicit_server(self):
        """Ventilation en utilisant un groupe explicitement nommé."""
        GroupLoader().load()
        self.host.write("""<?xml version="1.0"?>
        <host name="foo" address="127.0.0.1" ventilation="Vigilo">
            <test name="all.Interface" weight="42" warning_weight="41">
                <arg name="label">eth0</arg>
                <arg name="ifname">eth0</arg>
            </test>
            <group>/Servers/Linux servers</group>
        </host>
        """)
        self.host.close()
        self.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts",
                                    "host.xml"))
        pprint.pprint(self.hostsConf)
        # L'attribut ventilation a été donné explicitement.
        self.assertEqual(self.hostsConf['foo']['serverGroup'], 'Vigilo')

    def test_missing_group_association(self):
        """Hôte associé à aucun groupe opérationnel."""
        self.host.write("""<?xml version="1.0"?>
        <host name="foo" address="127.0.0.1" ventilation="Vigilo">
            <test name="all.Interface" weight="41" warning_weight="42">
                <arg name="label">eth0</arg>
                <arg name="ifname">eth0</arg>
            </test>
        </host>
        """)
        self.host.close()
        # Un hôte doit toujours être associé à au moins un <group>.
        # La vérification ne peut pas être faite au niveau du schéma XSD
        # car on perdrait alors la possibilité d'utiliser un ordre quelconque
        # pour les balises de définition d'un hôte.
        self.assertRaises(ParsingError, self.hostfactory._loadhosts,
            os.path.join(self.tmpdir, "hosts", "host.xml"))

    def test_test_missing_args(self):
        """Ajout d'un test auquel il manque des arguments sur un hôte."""
        # Le test "TCP" nécessite normalement un argument "port".
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
            <test name="TCP"/>
            <group>/Servers</group>
        </host>""")
        self.host.close()
        # Une exception TypeError indiquant qu'il n'y pas assez d'arguments
        # doit être levée.
        self.assertRaises(VigiConfError,
            self.hostfactory._loadhosts,
            os.path.join(self.tmpdir, "hosts", "host.xml")
        )

    def test_test_additional_args(self):
        """Ajout d'un test avec trop d'arguments sur un hôte."""
        # Le test "TCP" n'accepte pas d'argument "unknown".
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
            <test name="TCP">
                <arg name="port">1234</arg>
                <arg name="unknown_arg"> ... </arg>
            </test>
            <group>/Servers</group>
        </host>""")
        self.host.close()
        # Une exception TypeError indiquant qu'un paramètre inconnu
        # a été passé doit être levée.
        self.assertRaises(VigiConfError,
            self.hostfactory._loadhosts,
            os.path.join(self.tmpdir, "hosts", "host.xml")
        )

    def test_class_after_template(self):
        """Les classes doivent pouvoir être déclarées après les templates"""
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
            <template>linux</template>
        </host>""")
        self.host.close()
        htpl = HostTemplate("linux")
        htpl.add_group("Linux servers")
        htpl.add_test("linux.RAID")
        self.hosttemplatefactory.register(htpl)
        try:
            self.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts",
                                        "host.xml"))
        except ParsingError as e:
            print(e)
            self.fail("L'ordre des balises class et template est important")
        self.assertTrue("RAID" in self.hostsConf["testserver1"]["services"],
                        "L'ordre des balises class et template est important")

    def test_attributes_before_template(self):
        """Les attributs doivent pouvoir être déclarés avant les templates"""
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
            <attribute name="snmpCommunity">new_community</attribute>
            <template>linux</template> <!-- should not reset to public -->
        </host>""")
        self.host.close()
        htpl = HostTemplate("linux")
        htpl.add_attribute("snmpCommunity", "public")
        htpl.add_group("Linux servers")
        self.hosttemplatefactory.register(htpl)
        self.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts",
                                    "host.xml"))
        self.assertEqual(self.hostsConf['testserver1']['snmpCommunity'],
                         "new_community")

    def test_attributes_reserved_value(self):
        """
        Les attributs ne doivent pas pouvoir utiliser un attribut réservé
        """
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1">
            <attribute name="dataSources">essai</attribute>
            <group>/Servers</group>
        </host>""")
        self.host.close()
        path = os.path.join(self.tmpdir, "hosts", "host.xml")
        self.assertRaises(ParsingError, self.hostfactory._loadhosts, path)

    def test_attributes_before_template_avail_in_template(self):
        """Si les attributs sont déclarés avant les templates, il doivent y être dispo"""
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
            <attribute name="attribute_in_conf">right_value</attribute>
            <template>linux</template>
        </host>""")
        self.host.close()
        from vigilo.vigiconf.lib.confclasses.test import Test
        class AttributeUsingTest(Test):
            def add_test(self):
                self.host.set_attribute(
                    "attribute_in_test",
                    self.host.get_attribute("attribute_in_conf", "wrong_value")
                )
        self.hosttemplatefactory.testfactory.tests["AttributeUsingTest"] = {
                "all": AttributeUsingTest}
        htpl = HostTemplate("linux")
        htpl.add_group("Linux servers")
        htpl.add_test("all.AttributeUsingTest")
        self.hosttemplatefactory.register(htpl)
        self.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts",
                                    "host.xml"))
        self.assertEqual(self.hostsConf['testserver1']['attribute_in_test'],
                         "right_value")

    def test_attributes_in_template(self):
        """Un test dans un template a accès aux attributs définis dans ce template."""
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
            <template>linux</template>
        </host>""")
        self.host.close()
        from vigilo.vigiconf.lib.confclasses.test import Test
        class AttributeUsingTest(Test):
            def add_test(self):
                self.host.set_attribute(
                    "attribute_in_test",
                    self.host.get_attribute("attribute_in_conf", "wrong_value")
                )
        self.hosttemplatefactory.testfactory.tests["AttributeUsingTest"] = {
                "all": AttributeUsingTest}
        htpl = HostTemplate("linux")
        htpl.add_group("Linux servers")
        htpl.add_attribute("attribute_in_conf", "right_value")
        htpl.add_test("all.AttributeUsingTest")
        self.hosttemplatefactory.register(htpl)
        self.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts",
                                    "host.xml"))
        self.assertEqual(self.hostsConf['testserver1']['attribute_in_test'],
                         "right_value")

    def test_test_args_list(self):
        """
        Listes de valeurs comme argument d'un test dans un hôte
        """
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1">
            <test name="all.ArgListTest">
                <arg name="multi">
                    <item>a</item>
                    <item>b</item>
                </arg>
            </test>
            <group>/Servers</group>
        </host>""")
        self.host.close()
        from vigilo.vigiconf.lib.confclasses.test import Test
        class ArgListTest(Test):
            args = None
            def add_test(self, multi):
                # On sauvegarde les valeurs dans un attribut de la classe
                # pour pouvoir ensuite tester leur contenu.
                ArgListTest.args = multi
        self.hostfactory.testfactory.tests["ArgListTest"] = {
                "all": ArgListTest}
        path = os.path.join(self.tmpdir, "hosts", "host.xml")
        self.hostfactory._loadhosts(path)
        self.assertEqual(ArgListTest.args, ('a', 'b'))


class ParseHostTemplate(unittest.TestCase):

    def setUp(self):
        setup_db()
        self.tmpdir = setup_tmpdir()
        os.mkdir(os.path.join(self.tmpdir, "hosttemplates"))
        os.mkdir(os.path.join(self.tmpdir, "hosts"))
        self.old_conf_path = settings["vigiconf"]["confdir"]
        settings["vigiconf"]["confdir"] = self.tmpdir
        testfactory = TestFactory(confdir=self.tmpdir)
        self.hosttemplatefactory = HostTemplateFactory(testfactory)
        self.hosttemplatefactory.path = [ os.path.join(self.tmpdir,
                                          "hosttemplates"), ]
        self.defaultht = open(os.path.join(self.tmpdir, "hosttemplates",
                              "default.xml"), "w")
        self.defaultht.write('<?xml version="1.0"?>\n<templates>'
                '<template name="default"></template></templates>')
        self.defaultht.close()
        self.ht = open(os.path.join(self.tmpdir, "hosttemplates",
                       "test.xml"), "w")

    def tearDown(self):
        # This has been overwritten in setUp, reset it
        settings["vigiconf"]["confdir"] = self.old_conf_path
        shutil.rmtree(self.tmpdir)
        teardown_db()

    def test_template(self):
        """Test the parsing of a basic template declaration"""
        self.ht.write("""<?xml version="1.0"?>\n<templates>"""
                      """<template name="test"></template></templates>""")
        self.ht.close()
        try:
            self.hosttemplatefactory.load_templates()
        except KeyError:
            self.fail("template is not properly parsed")
        self.assertTrue("test" in self.hosttemplatefactory.templates,
               "template is not properly parsed")

    def test_attribute(self):
        self.ht.write("""<?xml version="1.0"?>
        <templates>
            <template name="test">
                <attribute name="testattr">testattrvalue</attribute>
            </template>
        </templates>""")
        self.ht.close()
        self.hosttemplatefactory.load_templates()
        attrs = self.hosttemplatefactory.templates["test"]["attributes"]
        self.assertTrue("testattr" in attrs and
                attrs["testattr"] == "testattrvalue",
                "The \"attribute\" tag is not properly parsed")

    def test_test(self):
        self.ht.write("""<?xml version="1.0"?>
        <templates>
        <template name="test">
            <test name="TestTest"/>
        </template>
        </templates>""")
        self.ht.close()
        try:
            self.hosttemplatefactory.load_templates()
        except KeyError:
            self.fail("The \"test\" tag is not properly parsed")
        self.assertEqual("TestTest",
               self.hosttemplatefactory.templates["test"]["tests"][0]["name"],
               "The \"test\" tag is not properly parsed")

    def test_test_args(self):
        """The \"test\" tag with arguments must be properly parsed"""
        self.ht.write("""<?xml version="1.0"?>
        <templates>
        <template name="test">
            <test name="TestTest">
                <arg name="TestArg1">TestValue1</arg>
                <arg name="TestArg2">TestValue2</arg>
            </test>
        </template>
        </templates>""")
        self.ht.close()
        try:
            self.hosttemplatefactory.load_templates()
        except KeyError:
            self.fail("The \"test\" tag with arguments is not properly parsed")
        tests = self.hosttemplatefactory.templates["test"]["tests"]
        self.assertEqual(len(tests), 1)
        self.assertEqual(tests[0]["name"], "TestTest")
        self.assertTrue("TestArg1" in tests[0]["args"])
        self.assertTrue("TestArg2" in tests[0]["args"])
        self.assertEqual(tests[0]["args"]["TestArg1"], "TestValue1")
        self.assertEqual(tests[0]["args"]["TestArg2"], "TestValue2")

    def test_test_args_list(self):
        """
        Listes de valeurs comme argument d'un test dans un modèle d'hôtes
        """
        self.ht.write("""<?xml version="1.0"?>
        <templates>
        <template name="test">
            <test name="TestTest">
                <arg name="multi">
                    <item>a</item>
                    <item>b</item>
                </arg>
            </test>
        </template>
        </templates>""")
        self.ht.close()
        try:
            self.hosttemplatefactory.load_templates()
        except KeyError:
            self.fail("The \"test\" tag with arguments is not properly parsed")
        tests = self.hosttemplatefactory.templates["test"]["tests"]
        self.assertEqual(len(tests), 1)
        self.assertEqual(tests[0]["name"], "TestTest")
        self.assertTrue("multi" in tests[0]["args"])
        self.assertEqual(tests[0]["args"]["multi"], ('a', 'b'))

    def test_group(self):
        self.ht.write("""<?xml version="1.0"?>
        <templates>
        <template name="test">
            <group>/Test group</group>
        </template>
        </templates>""")
        self.ht.close()
        self.hosttemplatefactory.load_templates()
        self.assertTrue("/Test group" in
                self.hosttemplatefactory.templates["test"]["groups"],
               "The \"group\" tag is not properly parsed")

    def test_parent(self):
        self.ht.write("""<?xml version="1.0"?>
        <templates>
            <template name="test1">
            </template>
            <template name="test2">
                <parent>test1</parent>
            </template>
        </templates>""")
        self.ht.close()
        self.hosttemplatefactory.load_templates()
        self.assertTrue("test1" in
                self.hosttemplatefactory.templates["test2"]["parent"],
               "The \"parent\" tag is not properly parsed")

