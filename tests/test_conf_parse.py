#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os, unittest, tempfile, shutil, glob, subprocess

from vigilo.common.conf import settings
settings.load_module(__name__)

import vigilo.vigiconf.conf as conf
from vigilo.vigiconf.lib.confclasses.host import Host
from vigilo.vigiconf.lib import ParsingError
from vigilo.vigiconf.loaders.group import GroupLoader

from confutil import reload_conf, setup_tmpdir, setup_path
from confutil import setup_db, teardown_db

class ValidateXSD(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        self.dtddir = os.path.join(conf.CODEDIR, "validation", "xsd")
        self.hdir = os.path.join(settings["vigiconf"].get("confdir"), "hosts")
        self.htdir = os.path.join(settings["vigiconf"].get("confdir"),
                        "hosttemplates")

    def test_host(self):
        """Validate the provided hosts against the XSD"""
        hosts = glob.glob(os.path.join(self.hdir, "*.xml"))
        for host in hosts:
            valid = subprocess.call(["xmllint", "--noout", "--schema",
                                    os.path.join(self.dtddir, "host.xsd"), host])
            assert valid == 0, "Validation of host \"%s\" failed" % os.path.basename(host)

    def test_hosttemplate(self):
        """Validate the provided hosttemplatess against the XSD"""
        hts = glob.glob(os.path.join(self.htdir, "*.xml"))
        for ht in hts:
            valid = subprocess.call(["xmllint", "--noout", "--schema",
                                    os.path.join(self.dtddir, "hosttemplate.xsd"), ht])
            assert valid == 0, "Validation of hosttemplate \"%s\" failed" % os.path.basename(ht)


class ParseHost(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        # Prepare temporary directory
        setup_db()
        self.tmpdir = setup_tmpdir()
        shutil.copytree(os.path.join(
                            settings["vigiconf"].get("confdir"), "general"),
                        os.path.join(self.tmpdir, "general"))
        shutil.copytree(os.path.join(
                        settings["vigiconf"].get("confdir"), "hosttemplates"),
                        os.path.join(self.tmpdir, "hosttemplates"))
        shutil.copytree(os.path.join(
                        settings["vigiconf"].get("confdir"), "groups"),
                        os.path.join(self.tmpdir, "groups"))
        os.mkdir(os.path.join(self.tmpdir, "hosts"))
        settings["vigiconf"]["confdir"] = self.tmpdir
        # We changed the paths, reload the factories
        reload_conf()
        self.host = open(os.path.join(self.tmpdir, "hosts", "host.xml"), "w")

    def tearDown(self):
        """Call after every test case."""
        # This has been overwritten in setUp, reset it
        setup_path()
        #settings["vigiconf"]["confdir"] = os.path.join(os.path.dirname(__file__), "..", "src", "conf.d")
        shutil.rmtree(self.tmpdir)
        teardown_db()

    def test_host(self):
        """Test the parsing of a basic host declaration"""
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
        </host>""")
        self.host.close()
        conf.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        assert conf.hostsConf.has_key("testserver1"), \
                "host is not properly parsed"
        assert conf.hostsConf["testserver1"]["name"] == "testserver1", \
                "host name is not properly parsed"
        assert conf.hostsConf["testserver1"]["address"] == "192.168.1.1", \
                "host address is not properly parsed"
        assert conf.hostsConf["testserver1"]["serverGroup"] == "Servers", \
                "host main group is not properly parsed"

    def test_host_whitespace(self):
        """Test the handling of whitespaces in a basic host declaration"""
        self.host.write("""<?xml version="1.0"?>
        <host name=" testserver1 " address=" 192.168.1.1 " ventilation=" Servers ">
        </host>""")
        self.host.close()
        conf.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        assert conf.hostsConf.has_key("testserver1"), \
                "host parsing does not handle whitespaces properly"

    def test_template(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
        <template>linux</template>
        </host>""")
        self.host.close()
        conf.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        assert "Linux servers" in conf.hostsConf["testserver1"]["otherGroups"], \
                "The \"template\" tag is not properly parsed"

    def test_template_whitespace(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
        <template> linux </template>
        </host>""")
        self.host.close()
        try:
            conf.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        except KeyError:
            self.fail("The \"template\" tag does not strip whitespaces")

    def test_attribute(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
        <attribute name="cpulist">2</attribute>
        </host>""")
        self.host.close()
        conf.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        assert conf.hostsConf["testserver1"].has_key("cpulist") and \
                conf.hostsConf["testserver1"]["cpulist"] == "2", \
                "The \"attribute\" tag is not properly parsed"

    def test_attribute_whitespace(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
        <attribute name=" cpulist "> 2 </attribute>
        </host>""")
        self.host.close()
        conf.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        assert conf.hostsConf["testserver1"].has_key("cpulist") and \
                conf.hostsConf["testserver1"]["cpulist"] == "2", \
                "The \"attribute\" tag parsing does not strip whitespaces"

    def test_tag_host(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
        <tag service="Host" name="important">2</tag>
        </host>""")
        self.host.close()
        conf.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        assert "tags" in conf.hostsConf["testserver1"] and \
               "important" in conf.hostsConf["testserver1"]["tags"] and \
                conf.hostsConf["testserver1"]["tags"]["important"] == "2", \
                "The \"tag\" tag for hosts is not properly parsed"

    def test_tag_service(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
        <tag service="UpTime" name="important">2</tag>
        </host>""")
        self.host.close()
        conf.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        assert "tags" in conf.hostsConf["testserver1"]["services"]["UpTime"] and \
               "important" in conf.hostsConf["testserver1"]["services"]["UpTime"]["tags"] and \
               conf.hostsConf["testserver1"]["services"]["UpTime"]["tags"]["important"] == "2", \
               "The \"tag\" tag for services is not properly parsed"

    def test_tag_whitespace(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
        <tag service=" Host " name=" important "> 2 </tag>
        </host>""")
        self.host.close()
        try:
            conf.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        except KeyError:
            self.fail("The \"tag\" tag parsing does not strip whitespaces")
        assert "tags" in conf.hostsConf["testserver1"] and \
               "important" in conf.hostsConf["testserver1"]["tags"] and \
               conf.hostsConf["testserver1"]["tags"]["important"] == "2", \
               "The \"tag\" tag parsing does not strip whitespaces"

    def test_trap(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
        <trap service="test.add_trap" key="test.name">test.label</trap>
        </host>""")
        self.host.close()
        conf.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        assert conf.hostsConf["testserver1"].has_key("trapItems") and \
                conf.hostsConf["testserver1"]["trapItems"]["test.add_trap"]["test.name"] == "test.label", \
                "The \"trap\" tag is not properly parsed"

    def test_trap_whitespace(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
        <trap service=" test.add_trap " key=" test.name "> test.label </trap>
        </host>""")
        self.host.close()
        conf.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        assert "trapItems" in conf.hostsConf["testserver1"] and \
               "test.add_trap" in conf.hostsConf["testserver1"]["trapItems"] and \
               "test.name" in conf.hostsConf["testserver1"]["trapItems"]["test.add_trap"] and \
               conf.hostsConf["testserver1"]["trapItems"]["test.add_trap"]["test.name"] == "test.label", \
               "The \"trap\" tag parsing does not strip whitespaces"

    def test_group(self):
        GroupLoader().load()
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
        <group>Linux servers</group>
        </host>""")
        self.host.close()
        conf.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        print conf.hostsConf["testserver1"]["otherGroups"]
        assert "/Servers/Linux servers" in conf.hostsConf["testserver1"]["otherGroups"], \
                "The \"group\" tag is not properly parsed"

    def test_group_whitespace(self):
        GroupLoader().load()
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
        <group> Linux servers </group>
        </host>""")
        self.host.close()
        conf.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        print conf.hostsConf["testserver1"]["otherGroups"]
        assert "/Servers/Linux servers" in conf.hostsConf["testserver1"]["otherGroups"], \
                "The \"group\" tag parsing does not strip whitespaces"

    def test_test(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
        <test name="Interface">
            <arg name="label">eth0</arg>
            <arg name="ifname">eth0</arg>
        </test>
        </host>""")
        self.host.close()
        conf.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        assert ('Interface eth0', 'service') in conf.hostsConf["testserver1"]["SNMPJobs"], \
                "The \"test\" tag is not properly parsed"

    def test_test_whitespace(self):
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
        <test name=" Interface ">
            <arg name=" label "> eth0 </arg>
            <arg name=" ifname "> eth0 </arg>
        </test>
        </host>""")
        self.host.close()
        conf.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        assert ('Interface eth0', 'service') in conf.hostsConf["testserver1"]["SNMPJobs"], \
                "The \"test\" tag parsing does not strip whitespaces"

    def test_ventilation_explicit_server(self):
        """Ventilation en utilisant un groupe explicitement nommé."""
        GroupLoader().load()
        self.host.write("""<?xml version="1.0"?>
        <host name="foo" address="127.0.0.1" ventilation="Servers">
            <arg name="label">eth0</arg>
            <arg name="ifname">eth0</arg>
        </host>
        """)
        self.host.close()
        conf.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        # L'attribut ventilation a été donné explicitement.
        self.assertEqual(conf.hostsConf['foo']['serverGroup'], 'Servers')

    def test_ventilation_server_from_abs_groups(self):
        """Ventilation déterminée depuis des groupes avec chemins absolus."""
        GroupLoader().load()
        self.host.write("""<?xml version="1.0"?>
        <host name="foo" address="127.0.0.1">
            <arg name="label">eth0</arg>
            <arg name="ifname">eth0</arg>
            <group>/Servers/Linux servers</group>
            <group>/Servers/AIX servers</group>
        </host>
        """)
        self.host.close()
        conf.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))
        # La racine des groupes est commune, donc on peut déterminer
        # le groupe à utiliser pour la ventilation.
        self.assertEqual(conf.hostsConf['foo']['serverGroup'], 'Servers')

    def test_ventilation_server_from_rel_groups(self):
        """Ventilation déterminée depuis des groupes avec chemins relatifs."""
        GroupLoader().load()
        self.host.write("""<?xml version="1.0"?>
        <host name="foo" address="127.0.0.1">
            <arg name="label">eth0</arg>
            <arg name="ifname">eth0</arg>
            <group>Linux servers</group>
            <group>AIX servers</group>
        </host>
        """)
        self.host.close()
        conf.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))

        # On vérifie que les chemins relatifs ont bien été transformés
        # en chemin absolus. Et comme la racine de ces chemins est commune,
        # le groupe de ventilation doit avoir été calculé correctement.
        assert ('/Servers/Linux servers' in conf.hostsConf['foo']['otherGroups'])
        assert ('/Servers/AIX servers' in conf.hostsConf['foo']['otherGroups'])
        self.assertEqual(conf.hostsConf['foo']['serverGroup'], 'Servers')

    def test_ventilation_missing_information(self):
        """Absence d'informations permettant de déterminer la ventilation."""
        self.host.write("""<?xml version="1.0"?>
        <host name="foo" address="127.0.0.1">
            <arg name="label">eth0</arg>
            <arg name="ifname">eth0</arg>
        </host>
        """)
        self.host.close()
        # Aucune information ne permet de déterminer la ventilation à appliquer.
        self.assertRaises(ParsingError, conf.hostfactory._loadhosts,
            os.path.join(self.tmpdir, "hosts", "host.xml"))

    def test_ventilation_conflicting_groups(self):
        """Conflit sur la ventilation à partir des groupes."""
        GroupLoader().load()
        self.host.write("""<?xml version="1.0"?>
        <host name="foo" address="127.0.0.1">
            <arg name="label">eth0</arg>
            <arg name="ifname">eth0</arg>
            <group>/Servers/Linux servers</group>
            <group>/P-F</group>
        </host>
        """)
        self.host.close()
        # Les groupes donnent 2 candidats pour la ventilation (Servers et P-F).
        # Le conflit doit lever une erreur d'analyse.
        self.assertRaises(ParsingError, conf.hostfactory._loadhosts,
            os.path.join(self.tmpdir, "hosts", "host.xml"))

    def test_test_missing_args(self):
        """Ajout d'un test auquel il manque des arguments sur un hôte."""
        # Le test "TCP" nécessite normalement un argument "port".
        self.host.write("""<?xml version="1.0"?>
        <host name="testserver1" address="192.168.1.1" ventilation="Servers">
        <test name="TCP"/>
        </host>""")
        self.host.close()
        # Une exception TypeError indiquant qu'il n'y pas assez d'arguments
        # doit être levée.
        self.assertRaises(TypeError,
            conf.hostfactory._loadhosts,
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
        </host>""")
        self.host.close()
        # Une exception TypeError indiquant qu'un paramètre inconnu
        # a été passé doit être levée.
        self.assertRaises(TypeError,
            conf.hostfactory._loadhosts,
            os.path.join(self.tmpdir, "hosts", "host.xml")
        )


class ParseHostTemplate(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        # Prepare temporary directory
        self.tmpdir = setup_tmpdir()
        shutil.copytree(os.path.join(
                            settings["vigiconf"].get("confdir"), "general"),
                        os.path.join(self.tmpdir, "general"))
        #shutil.copytree(os.path.join(
        #                    settings["vigiconf"].get("confdir"), "hosttemplates"),
        #                os.path.join(self.tmpdir, "hosttemplates"))
        os.mkdir(os.path.join(self.tmpdir, "hosttemplates"))
        os.mkdir(os.path.join(self.tmpdir, "hosts"))
        settings["vigiconf"]["confdir"] = self.tmpdir
        # We changed the paths, reload the factories
        reload_conf()
        conf.hosttemplatefactory.path = [os.path.join(self.tmpdir, "hosttemplates"),]
        self.defaultht = open(os.path.join(self.tmpdir, "hosttemplates", "default.xml"), "w")
        self.defaultht.write('<?xml version="1.0"?>\n<templates><template name="default"></template></templates>')
        self.defaultht.close()
        self.ht = open(os.path.join(self.tmpdir, "hosttemplates", "test.xml"), "w")

    def tearDown(self):
        """Call after every test case."""
        # This has been overwritten in setUp, reset it
        setup_path()
        shutil.rmtree(self.tmpdir)


    def test_template(self):
        """Test the parsing of a basic template declaration"""
        self.ht.write("""<?xml version="1.0"?>\n<templates><template name="test"></template></templates>""")
        self.ht.close()
        try:
            conf.hosttemplatefactory.load_templates()
        except KeyError:
            self.fail("template is not properly parsed")
        assert "test" in conf.hosttemplatefactory.templates, \
               "template is not properly parsed"

    def test_template_whitespace(self):
        self.ht.write("""<?xml version="1.0"?>\n<templates><template name=" test "></template></templates>""")
        self.ht.close()
        try:
            conf.hosttemplatefactory.load_templates()
        except KeyError:
            self.fail("template parsing does not strip whitespaces")
        assert "test" in conf.hosttemplatefactory.templates, \
               "template parsing does not strip whitespaces"

    def test_attribute(self):
        self.ht.write("""<?xml version="1.0"?>
                <templates>
                    <template name="test">
                        <attribute name="testattr">testattrvalue</attribute>
                    </template>
                </templates>""")
        self.ht.close()
        conf.hosttemplatefactory.load_templates()
        assert "testattr" in conf.hosttemplatefactory.templates["test"]["attributes"] and \
               conf.hosttemplatefactory.templates["test"]["attributes"]["testattr"] == "testattrvalue", \
               "The \"attribute\" tag is not properly parsed"

    def test_attribute_whitespace(self):
        self.ht.write("""<?xml version="1.0"?>
                <templates>
                    <template name="test">
                        <attribute name=" testattr "> testattrvalue </attribute>
                    </template>
                </templates>
                """)
        self.ht.close()
        conf.hosttemplatefactory.load_templates()
        assert "testattr" in conf.hosttemplatefactory.templates["test"]["attributes"] and \
               conf.hosttemplatefactory.templates["test"]["attributes"]["testattr"] == "testattrvalue", \
               "The \"attribute\" tag parsing does not strip whitespaces"

    def test_test(self):
        self.ht.write("""<?xml version="1.0"?>
                <templates>
                <template name="test">
                    <test name="TestTest"/>
                </template>
                </templates>""")
        self.ht.close()
        try:
            conf.hosttemplatefactory.load_templates()
        except KeyError:
            self.fail("The \"test\" tag is not properly parsed")
        assert {"name": "TestTest"} in conf.hosttemplatefactory.templates["test"]["tests"], \
               "The \"test\" tag is not properly parsed"

    def test_test_args(self):
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
            conf.hosttemplatefactory.load_templates()
        except KeyError:
            self.fail("The \"test\" tag with arguments is not properly parsed")
        assert len(conf.hosttemplatefactory.templates["test"]["tests"]) == 1 and \
               conf.hosttemplatefactory.templates["test"]["tests"][0]["name"] == "TestTest" and \
               "TestArg1" in conf.hosttemplatefactory.templates["test"]["tests"][0]["args"] and \
               "TestArg2" in conf.hosttemplatefactory.templates["test"]["tests"][0]["args"] and \
               conf.hosttemplatefactory.templates["test"]["tests"][0]["args"]["TestArg1"] == "TestValue1" and \
               conf.hosttemplatefactory.templates["test"]["tests"][0]["args"]["TestArg2"] == "TestValue2", \
               "The \"test\" tag with arguments is not properly parsed"

    def test_test_whitespace(self):
        self.ht.write("""<?xml version="1.0"?>
                <templates>
                <template name="test">
                    <test name=" TestTest ">
                        <arg name=" TestArg1 "> TestValue1 </arg>
                        <arg name=" TestArg2 "> TestValue2 </arg>
                    </test>
                </template>
                </templates>""")
        self.ht.close()
        try:
            conf.hosttemplatefactory.load_templates()
        except KeyError:
            self.fail("The \"test\" tag parsing does not strip whitespaces")
        assert len(conf.hosttemplatefactory.templates["test"]["tests"]) == 1 and \
               conf.hosttemplatefactory.templates["test"]["tests"][0]["name"] == "TestTest" and \
               "TestArg1" in conf.hosttemplatefactory.templates["test"]["tests"][0]["args"] and \
               "TestArg2" in conf.hosttemplatefactory.templates["test"]["tests"][0]["args"] and \
               conf.hosttemplatefactory.templates["test"]["tests"][0]["args"]["TestArg1"] == "TestValue1" and \
               conf.hosttemplatefactory.templates["test"]["tests"][0]["args"]["TestArg2"] == "TestValue2", \
               "The \"test\" tag parsing does not strip whitespaces"

    def test_group(self):
        self.ht.write("""<?xml version="1.0"?>
                <templates>
                <template name="test">
                    <group>Test group</group>
                </template>
                </templates>""")
        self.ht.close()
        conf.hosttemplatefactory.load_templates()
        assert "Test group" in conf.hosttemplatefactory.templates["test"]["groups"], \
               "The \"group\" tag is not properly parsed"

    def test_group_whitespace(self):
        self.ht.write("""<?xml version="1.0"?>
                <templates>
                <template name="test">
                    <group> Test group </group>
                </template>
                </templates>""")
        self.ht.close()
        conf.hosttemplatefactory.load_templates()
        assert "Test group" in conf.hosttemplatefactory.templates["test"]["groups"], \
               "The \"group\" tag parsing does not strip whitespaces"

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
        conf.hosttemplatefactory.load_templates()
        assert "test1" in conf.hosttemplatefactory.templates["test2"]["parent"], \
               "The \"parent\" tag is not properly parsed"

    def test_parent_whitespace(self):
        self.ht.write("""<?xml version="1.0"?>
            <templates>
                <template name="test1">
                </template>
                <template name="test2">
                    <parent> test1 </parent>
                </template>
            </templates>""")
        self.ht.close()
        try:
            conf.hosttemplatefactory.load_templates()
        except KeyError:
            self.fail("The \"parent\" tag parsing does not strip whitespaces")
        assert "test1" in conf.hosttemplatefactory.templates["test2"]["parent"], \
               "The \"parent\" tag parsing does not strip whitespaces"

# vim:set expandtab tabstop=4 shiftwidth=4:
