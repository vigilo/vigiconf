#!/usr/bin/env python
"""
Test that the dispatchator works properly
"""

import sys, os, unittest, tempfile, shutil, glob, re

from vigilo.common.conf import settings
from vigilo.models.tables import MapGroup

import vigilo.vigiconf.conf as conf
from vigilo.vigiconf.lib.confclasses.host import Host
from vigilo.vigiconf.lib import dispatchmodes

from helpers import reload_conf, setup_tmpdir
from helpers import setup_deploy_dir, teardown_deploy_dir
from helpers import setup_db, teardown_db


class DispatchatorRemote(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        setup_db()

        # Prepare necessary directories
        # TODO: commenter les divers repertoires
        setup_deploy_dir()
        conf.appsGroupsByServer = {
                    'interface' : {
                        'Servers': ['localhost', 'localhost2'],
                    },
                    'collect' : {
                        'Servers': ['localhost', 'localhost2'],
                    },
                }

        self.host = Host(conf.hostsConf, "dummy", u"testserver1", u"192.168.1.1", u"Servers")
        test_list = conf.testfactory.get_test("UpTime", self.host.classes)
        self.host.add_tests(test_list)
        self.dispatchator = dispatchmodes.getinstance()
        # Disable qualification, validation, stop and start scripts
        for app in self.dispatchator.applications:
            app.validation = None
            app.start_command = None
            app.stop_command = None
        # Don't check the installed revisions
        self.dispatchator.force = True

    def tearDown(self):
        """Call after every test case."""
        teardown_db()
        teardown_deploy_dir()

    def test_list_servers(self):
        servers = self.dispatchator.listServers()
        self.assertEquals([u"localhost", u"localhost2"], sorted(list(servers)))

    def test_app_servers(self):
        for app in self.dispatchator.applications:
            servers = self.dispatchator.getServersForApp(app)
            self.assertEquals([u"localhost", u"localhost2"], sorted(list(servers)))

# vim:set expandtab tabstop=4 shiftwidth=4:
