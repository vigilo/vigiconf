#!/usr/bin/env python
"""
Test that the dispatchator works properly
"""

import sys, os, unittest, tempfile, shutil, glob, re
from pprint import pprint

import conf
import dispatchator
from lib.confclasses.host import Host
from lib import dispatchmodes


class Dispatchator(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        conf.confDir = "../src/conf.d"
        conf.templatesDir = "../src/conf.d/filetemplates"
        conf.dataDir = "../src"
        # Prepare necessary directories
        self.tmpdir = tempfile.mkdtemp()
        conf.libDir = self.tmpdir
        self.basedir = os.path.join(self.tmpdir, "deploy")
        os.mkdir(self.basedir)
        conf.baseConfDir = os.path.join(self.tmpdir, "confmgr-conf")
        os.mkdir(conf.baseConfDir)
        for dir in [ "new", "old", "prod" ]:
            os.mkdir( os.path.join(conf.baseConfDir, dir) )
        # Create necessary files
        os.mkdir( os.path.join(self.tmpdir, "revisions") )
        revs = open( os.path.join(self.tmpdir, "revisions", "localhost.revisions"), "w")
        revs.close()
        os.mkdir( os.path.join(self.basedir, "localhost") )
        revs = open( os.path.join(self.basedir, "localhost", "revisions.txt"), "w")
        revs.close()
        # Load the configuration
        conf.loadConf()
        conf.silent = True
        # Deploy on the localhost only -> switch to Community Edition
        delattr(conf, "appsGroupsByServer")
        self.host = Host("testserver1", "192.168.1.1", "Servers")
        self.host.add_test("UpTime")
        self.dispatchator = dispatchmodes.getinstance()
        # Disable qualification, validation, stop and start scripts
        for app in self.dispatchator.getApplications():
            app.setQualificationMethod("")
            app.setValidationMethod("")
            app.setStopMethod("")
            app.setStartMethod("")
        # Don't check the installed revisions
        self.dispatchator.setModeForce(True)

    def tearDown(self):
        """Call after every test case."""
        # Cannot use shutil.rmtree because some files belong to root (created with sudo)
        os.system("sudo rm -rf "+self.tmpdir)

    def test_deploy(self):
        """Globally test the deployment"""
        self.dispatchator.deploy()

    def test_restart(self):
        """Globally test the restart"""
        # Create necessary file
        revs = open( os.path.join(conf.baseConfDir, "new", "revisions.txt"), "w")
        revs.close()
        self.dispatchator.restart()



# vim:set expandtab tabstop=4 shiftwidth=4:
