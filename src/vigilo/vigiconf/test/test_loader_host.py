# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# pylint: disable-msg=C0111,W0212,R0904
# Copyright (C) 2006-2014 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Test du chargeur de configuration en base
"""
from __future__ import absolute_import

import os
import shutil
import unittest

import vigilo.vigiconf.conf as conf
from vigilo.common.conf import settings
settings.load_module(__name__)

from vigilo.models.session import DBSession

from vigilo.models.tables import Host, ConfItem, ConfFile

from vigilo.vigiconf.loaders.group import GroupLoader
from vigilo.vigiconf.loaders.host import HostLoader
from vigilo.vigiconf.lib.confclasses.host import Host as ConfHost
from vigilo.vigiconf.lib import ParsingError

from .helpers import setup_db, teardown_db, DummyRevMan, setup_tmpdir


class TestLoader(unittest.TestCase):

    def setUp(self):
        setup_db()
        self.tmpdir = setup_tmpdir()
        # attention, le fichier dummy.xml doit exister ou l'hôte sera supprimé
        # juste après avoir été inséré
        self.old_conf_dir = settings["vigiconf"]["confdir"]
        settings["vigiconf"]["confdir"] = self.tmpdir
        open(os.path.join(self.tmpdir, "dummy.xml"), "w").close() # == touch
        self.host = ConfHost(
            conf.hostsConf,
            os.path.join(self.tmpdir, "dummy.xml"),
            "testserver1",
            "192.168.1.1",
            "Servers",
        )
        self.rm = DummyRevMan()
        grouploader = GroupLoader()
        self.hostloader = HostLoader(grouploader, self.rm)

    def tearDown(self):
        teardown_db()
        shutil.rmtree(self.tmpdir)
        settings["vigiconf"]["confdir"] = self.old_conf_dir

    def test_warning_weight_forbidden(self):
        """Valeur de warning_weight < weight est interdite."""
        self.host.add_external_sup_service("Interface eth0")
        host_dict = conf.hostsConf[u'testserver1']
        host_dict["default_service_weight"] = 1
        host_dict["default_service_warning_weight"] = 3
        print host_dict
        try:
            self.hostloader.load()
        except ParsingError, e:
            pass
        except Exception, e:
            self.fail("Excepted a ParsingError, got %s" % type(e))
        else:
            self.fail("Expected a ParsingError")

    def test_warning_weight_forbidden2(self):
        """Valeur de warning_weight < weight surchargée est interdite."""
        self.host.add_external_sup_service("Interface eth0", weight=12)
        host_dict = conf.hostsConf[u'testserver1']
        host_dict["default_service_weight"] = 42
        host_dict["default_service_warning_weight"] = 41
        print host_dict
        try:
            self.hostloader.load()
        except ParsingError, e:
            pass
        except Exception, e:
            self.fail("Excepted a ParsingError, got %s" % type(e))
        else:
            self.fail("Expected a ParsingError")

    def test_inexistent_group(self):
        host_dict = conf.hostsConf[u'testserver1']
        host_dict['otherGroups'].add(u'Inexistent group')
        error = None
        try:
            self.hostloader.load()
        except ParsingError, e:
            error = e.args[0]
        except Exception, e:
            self.fail("Excepted a ParsingError, got %s" % type(e))
        else:
            self.fail("Expected a ParsingError")
        # On ne peut pas tester toute la chaîne à cause des traductions
        self.assertTrue("Inexistent group" in error)
        self.assertTrue("testserver1" in error)

    def test_export_hosts_db(self):
        self.hostloader.load()
        h = Host.by_host_name(u'testserver1')
        self.assertNotEqual(h, None)
        self.assertEqual(h.name, u'testserver1')
        self.assertEqual(h.address, u'192.168.1.1')

    def test_remove_conffile_on_missing_files(self):
        ConfFile.get_or_create(u"dummy2.xml")
        self.hostloader.load()
        self.assertEqual(0, DBSession.query(ConfFile).filter_by(
                            name=u"dummy2.xml").count())

    def test_remove_conffile_on_svn_remove(self):
        ConfFile.get_or_create(u"dummy2.xml")
        dummy_file = os.path.join(self.tmpdir, "dummy2.xml")
        open(dummy_file, "w").close()
        self.rm.dummy_status["removed"] = [dummy_file]
        self.hostloader.load()
        self.assertEqual(0, DBSession.query(ConfFile).filter_by(
                            name=u"dummy2.xml").count())

    def test_remove_conffile_on_parent_svn_remove(self):
        ConfFile.get_or_create(u"dummydir/dummy2.xml")
        os.mkdir(os.path.join(self.tmpdir, "dummydir"))
        open(os.path.join(self.tmpdir, "dummydir", "dummy2.xml"), "w").close()
        self.rm.dummy_status["removed"] = [os.path.join(self.tmpdir, "dummydir"), ]
        self.hostloader.load()
        self.assertEqual(0, DBSession.query(ConfFile).filter_by(
                            name=u"dummydir/dummy2.xml").count())
