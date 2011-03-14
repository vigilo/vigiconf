#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test that the remote dispatchator works properly
Ces tests ne fonctionneront que dans Vigilo Enterprise Edition
"""

import os
import unittest
import shutil

from vigilo.common.conf import settings

import vigilo.vigiconf.conf as conf
from vigilo.vigiconf.lib.confclasses.host import Host
from vigilo.vigiconf.lib.dispatchator import make_dispatchator

from helpers import setup_tmpdir
from helpers import setup_deploy_dir
from helpers import setup_db, teardown_db


class DispatchatorRemote(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        setup_db()
        self.tmpdir = setup_tmpdir()
        settings["vigiconf"]["confdir"] = os.path.join(self.tmpdir, "conf.d")
        os.mkdir(settings["vigiconf"]["confdir"])

        # créer le fichier ssh_config
        os.mkdir(os.path.join(self.tmpdir, "ssh"))
        open(os.path.join(self.tmpdir, "ssh", "ssh_config"), "w").close()

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

        self.host = Host(conf.hostsConf, "dummy", u"testserver1",
                         u"192.168.1.1", u"Servers")
        test_list = conf.testfactory.get_test("UpTime", self.host.classes)
        self.host.add_tests(test_list)
        self.dispatchator = make_dispatchator()
        # Disable qualification, validation, stop and start scripts
        for app in self.dispatchator.apps_mgr.applications:
            app.validation = None
            app.start_command = None
            app.stop_command = None
        # Don't check the installed revisions
        self.dispatchator.force = True

    def tearDown(self):
        """Call after every test case."""
        conf.hostfactory.hosts = {}
        conf.hostsConf = conf.hostfactory.hosts
        teardown_db()
        shutil.rmtree(self.tmpdir)


# vim:set expandtab tabstop=4 shiftwidth=4:
