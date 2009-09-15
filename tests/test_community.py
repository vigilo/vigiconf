#!/usr/bin/env python
"""
Test that the ConfMgr works in Community Edition
"""

import sys
import os
import unittest
import tempfile
import shutil
import glob
import re
import socket

import vigilo.vigiconf.conf as conf
import vigilo.vigiconf.generator as generator
import vigilo.vigiconf.dispatchator as dispatchator
from vigilo.vigiconf.lib.dispatchmodes.local import DispatchatorLocal
from vigilo.vigiconf.lib.dispatchmodes.remote import DispatchatorRemote
from vigilo.vigiconf.lib.server import ServerFactory
from vigilo.vigiconf.lib.servertypes.local import ServerLocal
from vigilo.vigiconf.lib.servertypes.remote import ServerRemote
from vigilo.vigiconf.lib.confclasses.host import Host
from vigilo.vigiconf.lib import dispatchmodes

from . import reload_conf, setup_tmpdir


class EnterpriseEdition(unittest.TestCase):
    """Test the Enterprise Edition aspects"""

    def setUp(self):
        """Call before every test case."""
        # Prepare temporary directory
        self.tmpdir = setup_tmpdir()
        self.basedir = os.path.join(self.tmpdir, "deploy")
        # Load the configuration
        reload_conf()
        self.host = Host(conf.hostsConf, "testserver1", "192.168.1.1", "Servers")
        # Create appsGroupsByServer mapping (Enterprise Edition)
        conf.appsGroupsByServer = {
                    "collect": {
                        "P-F":     ["sup.example.com"],
                        "Servers": ["sup.example.com"],
                    },
                    "metrology": {
                        "P-F":     ["sup.example.com"],
                        "Servers": ["sup.example.com"],
                    },
                    "corrpres": {
                        "P-F":     ["sup.example.com"],
                        "Servers": ["sup.example.com"],
                    },
                    "reporting": {
                        "P-F":     ["sup.example.com"],
                        "Servers": ["sup.example.com"],
                    },
                }
        self.mapping = generator.getventilation()

    def tearDown(self):
        """Call after every test case."""
        shutil.rmtree(self.tmpdir)

    def test_ventilator_ent(self):
        """The supervision server in E.E. must not be the localhost"""
        for app, appserver in self.mapping[self.host.name].iteritems():
            assert appserver != "localhost", \
                "The supevision server in the Enterprise Edition for the " \
               +"%s application is the localhost" % app

    def test_generator_ent(self):
        """Generation directory in E.E. must be named after the sup server"""
        test_list = conf.testfactory.get_test("UpTime", self.host.classes)
        self.host.add_tests(test_list)
        generator.generate(self.basedir)
        assert os.path.exists(os.path.join(self.basedir, "sup.example.com",
                                           "nagios.cfg"))

    def test_dispatchator_ent(self):
        """The dispatchator instance in E.E. must be remote"""
        # Create a dummy ssh_config file
        os.mkdir( os.path.join(self.tmpdir, "db") )
        ssh_cf = open( os.path.join(self.tmpdir, "db", "ssh_config"), "w")
        ssh_cf.close()
        _dispatchator = dispatchmodes.getinstance()
        assert isinstance(_dispatchator, DispatchatorRemote), \
                "The dispatchator instance in the Enterprise Edition is " \
               +"not an instance of DispatchatorRemote"

    def test_serverfactory_ent(self):
        """ServerFactory must return ServerRemote instances for
           non-local hostnames"""
        # Declare temp dir
        conf.libDir = self.tmpdir
        # Create a dummy ssh_config file
        os.mkdir( os.path.join(self.tmpdir, "db") )
        ssh_cf = open( os.path.join(self.tmpdir, "db", "ssh_config"), "w")
        ssh_cf.close()
        # Start the actual test
        _serverfactory = ServerFactory()
        _server = _serverfactory.makeServer("sup.example.com")
        assert isinstance(_server, ServerRemote), \
                "The ServerFactory does not create ServerRemote instances " \
               +"for non-local hostnames"


class CommunityEdition(unittest.TestCase):
    """Test the Community Edition aspects"""

    def setUp(self):
        """Call before every test case."""
        # Prepare temporary directory
        self.tmpdir = setup_tmpdir()
        self.basedir = os.path.join(self.tmpdir, "deploy")
        # Load the configuration
        reload_conf()
        delattr(conf, "appsGroupsByServer") # Become the Community(tm) :)
        self.host = Host(conf.hostsConf, "testserver1", "192.168.1.1", "Servers")
        self.mapping = generator.getventilation()

    def tearDown(self):
        """Call after every test case."""
        shutil.rmtree(self.tmpdir)

    def test_ventilator_com(self):
        """The supervision server in C.E. must always be the localhost"""
        for app, appserver in self.mapping[self.host.name].iteritems():
            assert appserver == "localhost", \
                "The supevision server in the Enterprise Edition for the " \
               +"%s application is not the localhost" % app

    def test_generator_com(self):
        """Test the generation in C.E."""
        test_list = conf.testfactory.get_test("UpTime", self.host.classes)
        self.host.add_tests(test_list)
        generator.generate(self.basedir)
        assert os.path.exists(os.path.join(self.basedir, "localhost",
                              "nagios.cfg"))

    def test_dispatchator_com(self):
        """The dispatchator instance in C.E. must be local"""
        _dispatchator = dispatchmodes.getinstance()
        assert isinstance(_dispatchator, DispatchatorLocal), \
                "The dispatchator instance in the Community Edition is " \
               +"not an instance of DispatchatorLocal"

    def test_serverfactory_localhost(self):
        """ServerFactory must return ServerLocal instances for localhost"""
        _serverfactory = ServerFactory()
        _server = _serverfactory.makeServer("localhost")
        assert isinstance(_server, ServerLocal), \
                "The ServerFactory does not create ServerLocal instances " \
               +"for localhost"

    def test_serverfactory_localname(self):
        """ServerFactory must return ServerLocal instances for the
           local hostname"""
        _localname = socket.gethostname()
        _serverfactory = ServerFactory()
        _server = _serverfactory.makeServer(_localname)
        assert isinstance(_server, ServerLocal), \
                "The ServerFactory does not create ServerLocal instances " \
               +"for the local hostname"

    def test_serverfactory_localfqdn(self):
        """ServerFactory must return ServerLocal instances for the
           local FQDN"""
        _localname = socket.getfqdn()
        _serverfactory = ServerFactory()
        _server = _serverfactory.makeServer(_localname)
        assert isinstance(_server, ServerLocal), \
                "The ServerFactory does not create ServerLocal instances " \
               +"for the local FQDN"



# vim:set expandtab tabstop=4 shiftwidth=4:
