#!/usr/bin/env python
"""
Test that the dispatchator works properly
"""

import sys, os, unittest, tempfile, shutil, glob, re

import vigilo.vigiconf.conf as conf
import vigilo.vigiconf.dispatchator as dispatchator
from vigilo.vigiconf.lib.confclasses.host import Host
from vigilo.vigiconf.lib import dispatchmodes

from confutil import reload_conf, setup_tmpdir


class Dispatchator(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        # Prepare necessary directories
        self.tmpdir = setup_tmpdir()
        self.basedir = os.path.join(self.tmpdir, "deploy")
        os.mkdir(self.basedir)
        conf.baseConfDir = os.path.join(self.tmpdir, "vigiconf-conf")
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
        # We changed the paths, reload the factories
        reload_conf()
        # Deploy on the localhost only -> switch to Community Edition
        delattr(conf, "appsGroupsByServer")
        self.host = Host(conf.hostsConf, "testserver1", "192.168.1.1", "Servers")
        test_list = conf.testfactory.get_test("UpTime", self.host.classes)
        self.host.add_tests(test_list)
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
        shutil.rmtree(self.tmpdir)
        # Restore baseConfDir
        conf.baseConfDir = "/tmp/vigiconf-conf"

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
