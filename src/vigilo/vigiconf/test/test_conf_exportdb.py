#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test du chargeur de configuration en base
"""


import os
import shutil
import unittest

import vigilo.vigiconf.conf as conf
from vigilo.common.conf import settings
settings.load_module(__name__)

from vigilo.vigiconf.loaders.group import GroupLoader
from vigilo.vigiconf.loaders.host import HostLoader
from vigilo.vigiconf.lib.confclasses.host import Host as ConfHost

from helpers import setup_db, teardown_db, DummyRevMan, setup_tmpdir

from vigilo.models.tables import Host
from vigilo.models.tables import ConfItem


class TestLoader(unittest.TestCase):

    def setUp(self):
        setup_db()
        self.tmpdir = setup_tmpdir()
        # attention, le fichier dummy.xml doit exister ou l'hôte sera supprimé
        # juste après avoir été inséré
        self.old_conf_dir = settings["vigiconf"]["confdir"]
        settings["vigiconf"]["confdir"] = self.tmpdir
        open(os.path.join(self.tmpdir, "dummy.xml"), "w").close() # == touch
        self.host = ConfHost(conf.hostsConf, "dummy.xml", "testserver1",
                             "192.168.1.1", "Servers")
        rm = DummyRevMan()
        grouploader = GroupLoader()
        self.hostloader = HostLoader(grouploader, rm)

    def tearDown(self):
        """Call after every test case."""
        conf.hostfactory.hosts = {}
        conf.hostsConf = conf.hostfactory.hosts
        teardown_db()
        shutil.rmtree(self.tmpdir)
        settings["vigiconf"]["confdir"] = self.old_conf_dir

    def test_export_hosts_db(self):
        self.hostloader.load()
        h = Host.by_host_name(u'testserver1')
        self.assertNotEqual(h, None)
        self.assertEqual(h.name, u'testserver1')
        self.assertEqual(h.address, u'192.168.1.1')

    def test_export_host_confitem(self):
        host_dict = conf.hostsConf[u'testserver1']
        host_dict['nagiosDirectives'] = {u"max_check_attempts": u"8",
                                         u"check_interval": u"2"}

        self.hostloader.load()

        ci = ConfItem.by_host_confitem_name(u"testserver1",
                                            u"max_check_attempts")
        self.assertNotEqual(ci, None, "confitem max_check_attempts must exist")
        self.assertEqual(ci.value, "8", "max_check_attempts=8")

        ci = ConfItem.by_host_confitem_name(u"testserver1", u"check_interval")
        self.assertNotEqual(ci, None, "confitem check_interval must exist")
        self.assertEquals(ci.value, "2", "check_interval=2")

    def test_export_service_confitem(self):
        self.host.add_external_sup_service("Interface eth0")
        host_dict = conf.hostsConf[u'testserver1']
        host_dict['nagiosSrvDirs'][u'Interface eth0'] = {
                            u"max_check_attempts": u"7",
                            u"retry_interval": u"3"}

        self.hostloader.load()

        ci = ConfItem.by_host_service_confitem_name(
                            u'testserver1', u'Interface eth0',
                            u"max_check_attempts")
        self.assertTrue(ci, "confitem max_check_attempts must exist")
        self.assertEquals(ci.value, "7", "max_check_attempts=7")

        ci = ConfItem.by_host_service_confitem_name(
                            u'testserver1', u'Interface eth0',
                            u"retry_interval")
        self.assertTrue(ci, "confitem retry_interval must exist")
        self.assertEquals(ci.value, "3", "retry_interval=3")



if __name__ == '__main__':
    unittest.main()
