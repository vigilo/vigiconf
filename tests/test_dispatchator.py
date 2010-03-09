#!/usr/bin/env python
"""
Test that the dispatchator works properly
"""

import sys, os, unittest, tempfile, shutil, glob, re

from vigilo.common.conf import settings

import vigilo.vigiconf.conf as conf
import vigilo.vigiconf.dispatchator as dispatchator
from vigilo.vigiconf.lib.confclasses.host import Host
from vigilo.vigiconf.lib import dispatchmodes

from confutil import reload_conf, setup_tmpdir
from confutil import setup_deploy_dir, teardown_deploy_dir


class Dispatchator(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        # Prepare necessary directories
        # TODO commenter les divers repertoires
        setup_deploy_dir()
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
        teardown_deploy_dir()

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
