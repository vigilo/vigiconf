#!/usr/bin/env python
# vim: set fileencoding=utf-8 sw=4 ts=4 et :
"""
Test that VigiConf works in Community Edition
"""

import sys
import os
import unittest
import tempfile
import shutil
import glob
import re
import socket

from vigilo.common.conf import settings

import vigilo.vigiconf.conf as conf
from vigilo.vigiconf.lib.generators import GeneratorManager
from vigilo.vigiconf.applications.nagios import Nagios
from vigilo.vigiconf.lib.dispatchator.local import DispatchatorLocal
from vigilo.vigiconf.lib.server.factory import ServerFactory
from vigilo.vigiconf.lib.server.local import ServerLocal
from vigilo.vigiconf.lib.confclasses.host import Host
from vigilo.vigiconf.lib.ventilation import get_ventilator
from vigilo.vigiconf.lib.loaders import LoaderManager
from vigilo.vigiconf.lib.dispatchator.factory import get_dispatchator_class

from vigilo.models.session import DBSession
from vigilo.models import tables
from vigilo.models.demo.functions import add_host

from helpers import setup_tmpdir, DummyRevMan
from helpers import setup_db, teardown_db


class CommunityEdition(unittest.TestCase):
    """Test the Community Edition aspects"""

    def setUp(self):
        """Call before every test case."""
        # Prepare temporary directory
        setup_db()
        self.tmpdir = setup_tmpdir()
        self.basedir = os.path.join(self.tmpdir, "deploy")

    def tearDown(self):
        """Call after every test case."""
        DBSession.expunge_all()
        teardown_db()
        conf.hostfactory.hosts = {}
        conf.hostsConf = conf.hostfactory.hosts
        shutil.rmtree(self.tmpdir)

    def test_ventilator_com(self):
        """The supervision server in C.E. must always be the localhost"""
        host = Host(conf.hostsConf, "dummy.xml", "testserver1",
                    "192.168.1.1", "Servers")
        nagios = Nagios()
        DBSession.add(tables.Application(name=u"nagios"))
        genmanager = GeneratorManager([nagios])
        ventilator = get_ventilator([nagios])
        mapping = ventilator.ventilate()
        mapping = ventilator.ventilation_by_appname(mapping)
        for app, appserver in mapping[host.name].iteritems():
            self.assertEqual(appserver, "localhost",
                "The supevision server in the Enterprise Edition for the "
                "%s application is not the localhost" % app)

    def test_generator_com(self):
        """Test the generation in C.E."""
        # attention, le fichier dummy.xml doit exister ou l'hôte sera supprimé
        # juste après avoir été inséré
        settings["vigiconf"]["confdir"] = self.tmpdir
        open(os.path.join(self.tmpdir, "dummy.xml"), "w").close() # == touch
        host = Host(conf.hostsConf, "dummy.xml", "testserver1",
                    "192.168.1.1", "Servers")
        test_list = conf.testfactory.get_test("UpTime", host.classes)
        host.add_tests(test_list)
        #add_host("testserver1")
        nagios = Nagios()
        #DBSession.add(tables.Application(name=u"nagios"))
        #DBSession.flush()
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
        """ServerFactory must return ServerLocal instances for the
           local hostname"""
        _localname = socket.gethostname()
        _serverfactory = ServerFactory()
        _server = _serverfactory.makeServer(_localname)
        self.assert_(isinstance(_server, ServerLocal),
                "The ServerFactory does not create ServerLocal instances "
                "for the local hostname")

    def test_serverfactory_localfqdn(self):
        """ServerFactory must return ServerLocal instances for the
           local FQDN"""
        _localname = socket.getfqdn()
        _serverfactory = ServerFactory()
        _server = _serverfactory.makeServer(_localname)
        self.assert_(isinstance(_server, ServerLocal),
                "The ServerFactory does not create ServerLocal instances "
                "for the local FQDN")



# vim:set expandtab tabstop=4 shiftwidth=4:
