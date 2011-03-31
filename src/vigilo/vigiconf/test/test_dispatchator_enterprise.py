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
from vigilo.models.session import DBSession
from vigilo.models.demo import functions as df

import vigilo.vigiconf.conf as conf
from vigilo.vigiconf.lib.confclasses.host import Host
from vigilo.vigiconf.lib.dispatchator import make_dispatchator
from vigilo.vigiconf.lib.dispatchator.remote import DispatchatorRemote
from vigilo.vigiconf.lib.dispatchator.factory import get_dispatchator_class
from vigilo.vigiconf.lib.application import ApplicationManager
from vigilo.vigiconf.lib.server.factory import get_server_manager
from vigilo.vigiconf.lib.server.remote import ServerRemote
from vigilo.vigiconf.applications.nagios import Nagios
from vigilo.vigiconf.applications.vigimap import VigiMap
from vigilo.vigiconf.applications.vigirrd import VigiRRD

from helpers import setup_tmpdir
from helpers import setup_deploy_dir
from helpers import setup_db, teardown_db


class DispatchatorRemoteTest(unittest.TestCase):

    def setUp(self):
        setup_db()
        self.tmpdir = setup_tmpdir()
        settings["vigiconf"]["confdir"] = os.path.join(self.tmpdir, "conf.d")
        os.mkdir(settings["vigiconf"]["confdir"])
        # créer le fichier ssh_config
        os.mkdir(os.path.join(self.tmpdir, "ssh"))
        open(os.path.join(self.tmpdir, "ssh", "ssh_config"), "w").close()
        # Version Entreprise
        conf.appsGroupsByServer = {}

    def tearDown(self):
        DBSession.expunge_all()
        teardown_db()
        shutil.rmtree(self.tmpdir)
        delattr(conf, "appsGroupsByServer")


    def test_get_class(self):
        self.assertEqual(get_dispatchator_class(), DispatchatorRemote)

    def test_restrict(self):
        """C{restrict}() doit limiter les serveurs à la liste choisie"""
        # ServerManager
        srv_mgr = get_server_manager()
        for i in range(1, 10):
            sname = "sup%s.example.com" % i
            srv_mgr.servers[sname] = ServerRemote(sname)
        # ApplicationManager
        app_mgr = ApplicationManager()
        n = Nagios()
        n.servers = {"sup1.example.com": None}
        vm = VigiMap()
        vm.servers = {"sup2.example.com": None}
        vr = VigiRRD()
        vr.servers = {"sup3.example.com": None}
        app_mgr.applications = [n, vm, vr]
        # Dispatchator
        d = DispatchatorRemote(app_mgr, None, srv_mgr, None)
        d.restrict(["sup1.example.com", "sup2.example.com"])
        self.assertEqual(sorted(srv_mgr.servers),
                         ["sup1.example.com", "sup2.example.com"])
        self.assertEqual(len(app_mgr.applications), 2)
        self.assertEqual(app_mgr.applications, [n, vm])

    def test_filter_disabled(self):
        """
        C{filter_disabled}() doit limiter la liste des serveurs aux actifs
        """
        srv_mgr = get_server_manager()
        for i in range(1, 10):
            sname = "sup%s.example.com" % i
            srv_mgr.servers[sname] = ServerRemote(sname)
            df.add_vigiloserver(sname)
        app_mgr = ApplicationManager()
        d = DispatchatorRemote(app_mgr, None, srv_mgr, None)
        for i in range(3, 10):
            v = df.add_vigiloserver("sup%s.example.com" % i)
            v.disabled = True
        DBSession.flush()
        d.filter_disabled()
        self.assertEqual(sorted(srv_mgr.servers),
                         ["sup1.example.com", "sup2.example.com"])

# vim:set expandtab tabstop=4 shiftwidth=4:
