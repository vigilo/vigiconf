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
from confutil import setup_db, teardown_db, create_vigiloserver
from confutil import setup_deploy_dir, teardown_deploy_dir

import transaction

class DeployScenario(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        # Prepare necessary directories
        # TODO: commenter les divers repertoires
        setup_deploy_dir()
        setup_db()
        create_vigiloserver(u'localhost')
        transaction.commit()
        
        # Deploy on the localhost only -> switch to Community Edition
        
        delattr(conf, "appsGroupsByServer")
        self.host = Host(conf.hostsConf, u"testserver1", u"192.168.1.1", u"Servers")
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
        teardown_db()

    def test_deploy(self):
        """Teste un scenario generation, deploiement, saveConfig"""
        
        self.dispatchator.generateConfig()
        
        self.dispatchator.deploy()
        
        self.dispatchator.saveToConfig()



# vim:set expandtab tabstop=4 shiftwidth=4:
