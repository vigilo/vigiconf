# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# pylint: disable-msg=C0111,W0212,R0904
# Copyright (C) 2006-2014 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>
from __future__ import absolute_import

import os
import unittest
import shutil
import glob
import subprocess

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

from .helpers import setup_tmpdir, setup_db, teardown_db


class TestTemplates(unittest.TestCase):
    def setUp(self):
        setup_db()
        self.tmpdir = setup_tmpdir()
        os.mkdir(os.path.join(self.tmpdir, "hosttemplates"))
        os.mkdir(os.path.join(self.tmpdir, "hosts"))
        self.old_conf_path = settings["vigiconf"]["confdir"]
        settings["vigiconf"]["confdir"] = self.tmpdir
        testfactory = TestFactory(confdir=self.tmpdir)
        self.htplfactory = HostTemplateFactory(testfactory)
        self.htplfactory.path = [ os.path.join(self.tmpdir,
                                          "hosttemplates"), ]
        self.htplfactory.register(HostTemplate("default"))
        self.hostfactory = HostFactory(
                        os.path.join(self.tmpdir, "hosts"),
                        self.htplfactory,
                        testfactory,
                      )
        self.hostsConf = self.hostfactory.hosts
        self.htplsConf = self.htplfactory.templates

    def tearDown(self):
        # This has been overwritten in setUp, reset it
        settings["vigiconf"]["confdir"] = self.old_conf_path
        shutil.rmtree(self.tmpdir)
        teardown_db()

    def xml(self, default=None, templates=None, hosts=None):
        if not default:
            default = '<?xml version="1.0"?>\n<templates><template name="default"/></templates>'
        if not templates:
            templates = '<?xml version="1.0"?>\n<templates/>'
        if not hosts:
            hosts = """<?xml version="1.0"?>
                        <host name="server">
                            <group>/Servers/Linux servers</group>
                        </host>"""

        f = open(os.path.join(self.tmpdir, "hosttemplates", "default.xml"), "w")
        f.write(default)
        f.close()

        f = open(os.path.join(self.tmpdir, "hosts", "host.xml"), "w")
        f.write(hosts)
        f.close()

        f = open(os.path.join(self.tmpdir, "hosttemplates", "test.xml"), "w")
        f.write(templates)
        f.close()

        GroupLoader().load()
        self.htplfactory.load_templates()
        self.hostfactory._loadhosts(os.path.join(self.tmpdir, "hosts", "host.xml"))

    def test_tags_inheritance(self):
        """Les tags peuvent être hérités depuis le template par défaut."""
        default = """<?xml version="1.0"?><templates>
                    <template name="default">
                        <test name="Ping"/>
                        <tag name="host_tag">host_value</tag>
                        <tag service="Ping" name="svc_tag">svc_value</tag>
                    </template></templates>"""
        self.xml(default)

        self.assertEqual(
            self.hostsConf['server']['tags'],
            {'host_tag': 'host_value'}
        )
        self.assertEqual(
            self.hostsConf['server']['services']['Ping']['tags'],
            {'svc_tag': 'svc_value'}
        )

    def test_tags_overrides(self):
        """Les tags de l'hôte ont la priorité sur ceux des templates."""
        hosts = """<?xml version="1.0"?>
                    <host name="server">
                        <group>/Servers/Linux servers</group>
                        <tag name="host_tag">host_value</tag>
                        <tag service="Ping" name="svc_tag">svc_value</tag>
                        <template>test</template>
                    </host>"""
        tpls = """<?xml version="1.0"?><templates>
                    <template name="test">
                        <tag name="host_tag">host_value_tpl</tag>
                        <tag service="Ping" name="svc_tag">svc_value_tpl</tag>
                        <test name="Ping"/>
                    </template></templates>"""
        self.xml(hosts=hosts, templates=tpls)

        self.assertEqual(
            self.hostsConf['server']['tags'],
            {'host_tag': 'host_value'}
        )
        self.assertEqual(
            self.hostsConf['server']['services']['Ping']['tags'],
            {'svc_tag': 'svc_value'}
        )

    def test_tags_host_without_service(self):
        """Exception si tag sur service inexistant depuis l'hôte."""
        hosts = """<?xml version="1.0"?>
                    <host name="server">
                        <tag service="Ping" name="svc_tag">svc_value</tag>
                    </host>"""
        try:
           self.xml(hosts=hosts)
           self.fail('A ParsingError exception was expected')
        except ParsingError:
            pass

    def test_tags_tpl_without_service(self):
        """Exception si tag sur service inexistant depuis le modèle."""
        hosts = """<?xml version="1.0"?>
                    <host name="server">
                        <group>/Servers/Linux servers</group>
                        <template>test</template>
                    </host>"""
        tpls = """<?xml version="1.0"?><templates>
                    <template name="test">
                        <tag service="Ping" name="svc_tag">svc_value_tpl</tag>
                    </template></templates>"""
        try:
           self.xml(hosts=hosts, templates=tpls)
           self.fail('A ParsingError exception was expected')
        except ParsingError:
            pass
