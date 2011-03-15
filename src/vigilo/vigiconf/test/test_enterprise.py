#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test that VigiConf works in Enterprise Edition

Ces tests ne fonctionneront que dans la version Entreprise
"""

import os
import unittest
import shutil

from vigilo.common.conf import settings

import vigilo.vigiconf.conf as conf
from vigilo.vigiconf.lib.generators import GeneratorManager
from vigilo.vigiconf.applications.nagios import Nagios
from vigilo.vigiconf.lib.dispatchator.remote import DispatchatorRemote
from vigilo.vigiconf.lib.server.factory import ServerFactory
from vigilo.vigiconf.lib.server.remote import ServerRemote
from vigilo.vigiconf.lib.confclasses.host import Host
from vigilo.vigiconf.lib.ventilation import get_ventilator
from vigilo.vigiconf.lib.dispatchator.factory import get_dispatchator_class
from vigilo.vigiconf.lib.server import get_server_manager
from vigilo.vigiconf.lib.exceptions import VigiConfError

from vigilo.models.session import DBSession
from vigilo.models import tables
from vigilo.models.demo import functions as df

from helpers import setup_tmpdir, DummyRevMan
from helpers import setup_db, teardown_db


class EnterpriseEdition(unittest.TestCase):
    """Test the Enterprise Edition aspects"""

    def setUp(self):
        """Call before every test case."""
        setup_db()
        # Prepare temporary directory
        self.tmpdir = setup_tmpdir()
        self.basedir = os.path.join(self.tmpdir, "deploy")
        # Create appsGroupsByServer mapping (Enterprise Edition)
        conf.appsGroupsByServer = {
                    "interface": {
                        "P-F":     [u"sup.example.com"],
                        "Servers": [u"sup.example.com"],
                    },
                    "collect": {
                        "P-F":     [u"sup.example.com"],
                        "Servers": [u"sup.example.com"],
                    },
                    "metrology": {
                        "P-F":     [u"sup.example.com"],
                        "Servers": [u"sup.example.com"],
                    },
                    "trap": {
                        "P-F":     [u"sup.example.com"],
                        "Servers": [u"sup.example.com"],
                    },
                    "correlation": {
                        "P-F":     [u"sup.example.com"],
                        "Servers": [u"sup.example.com"],
                    },
                }

    def tearDown(self):
        """Call after every test case."""
        DBSession.expunge_all()
        teardown_db()
        conf.hostfactory.hosts = {}
        conf.hostsConf = conf.hostfactory.hosts
        delattr(conf, "appsGroupsByServer")
        shutil.rmtree(self.tmpdir)

    def test_ventilator_ent(self):
        """The supervision server in E.E. must not be the localhost"""
        # Load the configuration
        host = Host(conf.hostsConf, "dummy.xml", "testserver1",
                    "192.168.1.1", "Servers")
        df.add_host("testserver1")
        vs = tables.VigiloServer(name=u"sup.example.com")
        DBSession.add(vs)
        nagios = Nagios()
        DBSession.add(tables.Application(name=u"nagios"))
        genmanager = GeneratorManager([nagios])
        ventilator = get_ventilator([nagios])
        mapping = ventilator.ventilate()
        mapping = ventilator.ventilation_by_appname(mapping)
        for app, appserver in mapping[host.name].iteritems():
            self.failIfEqual(appserver, "localhost",
                "The supervision server in the Enterprise Edition for the " \
                "%s application is the localhost" % app)

    def test_generator_ent(self):
        """Generation directory in E.E. must be named after the sup server"""
        host = Host(conf.hostsConf, "dummy.xml", "testserver1",
                    "192.168.1.1", "Servers")
        # attention, le fichier dummy.xml doit exister ou l'hôte sera supprimé
        # juste après avoir été inséré
        settings["vigiconf"]["confdir"] = self.tmpdir
        open(os.path.join(self.tmpdir, "dummy.xml"), "w").close() # == touch
        # créer le fichier ssh_config
        settings["vigiconf"]["confdir"] = os.path.join(self.tmpdir, "conf.d")
        os.mkdir(settings["vigiconf"]["confdir"])
        os.mkdir(os.path.join(self.tmpdir, "ssh"))
        open(os.path.join(self.tmpdir, "ssh", "ssh_config"), "w").close()
        # ajout d'un test
        test_list = conf.testfactory.get_test("UpTime", host.classes)
        host.add_tests(test_list)
        # génération
        nagios = Nagios()
        DBSession.add(tables.Application(name=u"nagios"))
        genmanager = GeneratorManager([nagios])
        genmanager.generate(DummyRevMan())
        self.assertTrue(os.path.exists(os.path.join(self.basedir,
                        "sup.example.com", "nagios", "nagios.cfg")))
        self.assertEqual([u"sup.example.com"], nagios.servers.keys())

    def test_dispatchator_ent(self):
        """The dispatchator instance in E.E. must be remote"""
        d_class = get_dispatchator_class()
        self.assertEqual(d_class, DispatchatorRemote,
                "The dispatchator instance in the Enterprise Edition "
                "must be an instance of DispatchatorRemote")

    def test_serverfactory_ent(self):
        """ServerFactory must return ServerRemote instances for
           non-local hostnames"""
        # créer le fichier ssh_config
        settings["vigiconf"]["confdir"] = os.path.join(self.tmpdir, "conf.d")
        os.mkdir(settings["vigiconf"]["confdir"])
        os.mkdir(os.path.join(self.tmpdir, "ssh"))
        open(os.path.join(self.tmpdir, "ssh", "ssh_config"), "w").close()
        # Start the actual test
        _serverfactory = ServerFactory()
        _server = _serverfactory.makeServer("sup.example.com")
        self.assert_(isinstance(_server, ServerRemote),
                "The ServerFactory does not create ServerRemote instances "
                "for non-local hostnames")


class ServerManagerRemoteTest(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        setup_db()
        # Create appsGroupsByServer mapping (Enterprise Edition)
        conf.appsGroupsByServer = {
                    "collect": {
                        "P-F":     [u"sup1.example.com", u"sup2.example.com"],
                        "Servers": [u"sup1.example.com", u"sup2.example.com"],
                    },
                }
        # Prepare temporary directory
        self.tmpdir = setup_tmpdir()
        # créer le fichier ssh_config
        settings["vigiconf"]["confdir"] = os.path.join(self.tmpdir, "conf.d")
        os.mkdir(settings["vigiconf"]["confdir"])
        os.mkdir(os.path.join(self.tmpdir, "ssh"))
        open(os.path.join(self.tmpdir, "ssh", "ssh_config"), "w").close()

    def tearDown(self):
        """Call after every test case."""
        DBSession.expunge_all()
        teardown_db()
        conf.hostfactory.hosts = {}
        conf.hostsConf = conf.hostfactory.hosts
        delattr(conf, "appsGroupsByServer")
        shutil.rmtree(self.tmpdir)

    def test_list(self):
        sm = get_server_manager()
        sm.list()
        self.assertEquals([u"sup1.example.com", u"sup2.example.com"],
                          sorted(list(sm.servers)))


class ServerRemoteTest(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        setup_db()
        # Prepare temporary directory
        self.tmpdir = setup_tmpdir()
        self.basedir = os.path.join(self.tmpdir, "deploy")
        # créer le fichier ssh_config
        settings["vigiconf"]["confdir"] = os.path.join(self.tmpdir, "conf.d")
        os.mkdir(settings["vigiconf"]["confdir"])
        os.mkdir(os.path.join(self.tmpdir, "ssh"))
        open(os.path.join(self.tmpdir, "ssh", "ssh_config"), "w").close()

    def tearDown(self):
        """Call after every test case."""
        DBSession.expunge_all()
        teardown_db()
        shutil.rmtree(self.tmpdir)

    def test_disable(self):
        df.add_vigiloserver("sup1.example.com")
        s = ServerRemote("sup1.example.com")
        s.disable()
        vs = tables.VigiloServer.by_vigiloserver_name(u"sup1.example.com")
        self.assertTrue(vs.disabled)

    def test_disable_not_in_db(self):
        s = ServerRemote("sup1.example.com")
        self.assertRaises(VigiConfError, s.disable)

    def test_disabled_already(self):
        s = ServerRemote("sup1.example.com")
        v = df.add_vigiloserver("sup1.example.com")
        v.disabled = True
        DBSession.flush()
        self.assertRaises(VigiConfError, s.disable)
        s.enable()

    def test_enable(self):
        s = ServerRemote("sup1.example.com")
        v = df.add_vigiloserver("sup1.example.com")
        v.disabled = True
        DBSession.flush()
        s.enable()
        v = tables.VigiloServer.by_vigiloserver_name(u"sup1.example.com")
        self.assertFalse(v.disabled)

    def test_enable_not_in_db(self):
        s = ServerRemote("sup1.example.com")
        self.assertRaises(VigiConfError, s.enable)

    def test_enable_already(self):
        s = ServerRemote("sup1.example.com")
        v = df.add_vigiloserver("sup1.example.com")
        self.assertRaises(VigiConfError, s.enable)

    def test_enable_delete_prev_ventilation(self):
        s = ServerRemote("sup1.example.com")
        v1 = df.add_vigiloserver("sup1.example.com")
        v2 = df.add_vigiloserver("sup2.example.com")
        v1.disabled = True
        h = df.add_host("host1")
        a = df.add_application("app1")
        # association précédente (quand v1 était actif)
        DBSession.add(tables.Ventilation(
                      host=h, application=a, vigiloserver=v1))
        # association de backup, ajoutée après
        DBSession.add(tables.Ventilation(
                      host=h, application=a, vigiloserver=v2))
        DBSession.flush()
        self.assertEqual(DBSession.query(tables.Ventilation).count(), 2)
        s.enable()
        self.assertEqual(DBSession.query(tables.Ventilation).count(), 1)
        ventil = DBSession.query(tables.Ventilation).first()
        self.assertEqual(ventil.idvigiloserver, v1.idvigiloserver)


# vim:set expandtab tabstop=4 shiftwidth=4:
