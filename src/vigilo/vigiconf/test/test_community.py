# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# pylint: disable-msg=C0111,W0212,R0904
# Copyright (C) 2006-2019 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Test that VigiConf works in Community Edition
"""
from __future__ import absolute_import

import os
import unittest
import shutil
import socket

from vigilo.common.conf import settings
from vigilo.models.session import DBSession
from vigilo.models import tables

import vigilo.vigiconf.conf as conf
from vigilo.vigiconf.lib.generators import GeneratorManager
from vigilo.vigiconf.applications.nagios import Nagios
from vigilo.vigiconf.lib.dispatchator.local import DispatchatorLocal
from vigilo.vigiconf.lib.server.factory import ServerFactory
from vigilo.vigiconf.lib.server.local import ServerLocal
from vigilo.vigiconf.lib.confclasses.host import Host
from vigilo.vigiconf.lib.confclasses.test import TestFactory
from vigilo.vigiconf.lib.ventilation import get_ventilator
from vigilo.vigiconf.lib.dispatchator.factory import get_dispatchator_class

from .helpers import setup_tmpdir, DummyRevMan
from .helpers import setup_db, teardown_db


class CommunityEdition(unittest.TestCase):
    """Test the Community Edition aspects"""

    def setUp(self):
        conf.load_general_conf() # Réinitialisation de la configuration
        setup_db()
        self.tmpdir = setup_tmpdir()
        self.basedir = os.path.join(self.tmpdir, "deploy")
        self.old_conf_dir = settings["vigiconf"]["confdir"]
        settings["vigiconf"]["confdir"] = os.path.join(self.tmpdir, "conf")
        os.makedirs(os.path.join(self.tmpdir, "conf"))

    def tearDown(self):
        DBSession.expunge_all()
        teardown_db()
        shutil.rmtree(self.tmpdir)
        settings["vigiconf"]["confdir"] = self.old_conf_dir

    def test_ventilator_com(self):
        """The monitoring server in C.E. must always be the localhost"""
        host = Host(conf.hostsConf, "dummy.xml", "testserver1",
                    "192.168.1.1", "Servers")
        nagios = Nagios()
        DBSession.add(tables.Application(name=u"nagios"))
        ventilator = get_ventilator([nagios])
        mapping = ventilator.ventilate()
        mapping = ventilator.ventilation_by_appname(mapping)
        for app, appserver in mapping[host.name].iteritems():
            self.assertEqual(appserver, "localhost",
                "The monitoring server in the Enterprise Edition for the "
                "%s application is not the local host" % app)

    def test_generator_com(self):
        """Test the generation in C.E."""
        host = Host(conf.hostsConf, "dummy.xml", "testserver1",
                    "192.168.1.1", "Servers")
        testfactory = TestFactory(confdir=os.path.join(self.tmpdir, "conf"))
        test_list = testfactory.get_test("all.UpTime")
        host.add_tests(test_list)
        nagios = Nagios()
        genmanager = GeneratorManager([nagios])
        genmanager.generate(DummyRevMan())
        self.assert_(os.path.exists(os.path.join(self.basedir, "localhost",
                     "nagios", "nagios.cfg")))

    def test_dispatchator_com(self):
        """The dispatchator instance in C.E. must be local"""
        d_class = get_dispatchator_class()
        self.assertEqual(d_class, DispatchatorLocal,
                "The dispatchator instance in the Community Edition must "
                "be an instance of DispatchatorLocal")

    def test_serverfactory_localhost(self):
        """ServerFactory must return ServerLocal instances for localhost"""
        _serverfactory = ServerFactory()
        _server = _serverfactory.makeServer("localhost")
        self.assert_(isinstance(_server, ServerLocal),
                "The ServerFactory does not create ServerLocal instances "
                "for localhost")

    def test_serverfactory_localname(self):
        """
        ServerFactory must return ServerLocal instances for the local hostname
        """
        _localname = socket.gethostname()
        _serverfactory = ServerFactory()
        _server = _serverfactory.makeServer(_localname)
        self.assert_(isinstance(_server, ServerLocal),
                "The ServerFactory does not create ServerLocal instances "
                "for the local hostname")

    def test_serverfactory_localfqdn(self):
        """
        ServerFactory must return ServerLocal instances for the local FQDN
        """
        _localname = socket.getfqdn()
        _serverfactory = ServerFactory()
        _server = _serverfactory.makeServer(_localname)
        self.assert_(isinstance(_server, ServerLocal),
                "The ServerFactory does not create ServerLocal instances "
                "for the local FQDN")
