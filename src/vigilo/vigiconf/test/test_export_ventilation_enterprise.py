#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test du chargeur de ventilation en base.
Ces tests ne fonctionneront quand dans Vigilo Enterprise Edition
"""


import os
import shutil
import unittest

import vigilo.vigiconf.conf as conf
from vigilo.common.conf import settings
settings.load_module(__name__)

from vigilo.vigiconf.lib.loaders import LoaderManager
from vigilo.vigiconf.loaders.group import GroupLoader
from vigilo.vigiconf.loaders.host import HostLoader
from vigilo.vigiconf.lib.confclasses.host import Host as ConfHost
from vigilo.vigiconf.applications.nagios import Nagios
from vigilo.vigiconf.applications.vigimap import VigiMap
from vigilo.vigiconf.lib.ventilation import get_ventilator

from helpers import setup_db, teardown_db, DummyRevMan, setup_tmpdir

from vigilo.models.tables import Ventilation, Application, VigiloServer
from vigilo.models.session import DBSession


class TestLoader(unittest.TestCase):

    def setUp(self):
        setup_db()
        self.tmpdir = setup_tmpdir()
        conf.appsGroupsByServer = {
                    "interface": {
                        "Servers": [u"sup.example.com"],
                    },
                    "collect": {
                        "Servers": [u"sup.example.com"],
                    },
                    "trap": {
                        "Servers": [u"sup.example.com"],
                    },
                }

    def tearDown(self):
        """Call after every test case."""
        conf.hostfactory.hosts = {}
        conf.hostsConf = conf.hostfactory.hosts
        teardown_db()
        shutil.rmtree(self.tmpdir)
        delattr(conf, "appsGroupsByServer")

    def test_export_ventilation_db(self):
        """
        Export de la ventilation en BdD.
        On ventile une première fois, puis on supprime une application et on
        re-ventile. L'application ne doit plus être ventilée en BdD
        """
        ConfHost(conf.hostsConf, "dummy.xml", "testserver1",
                 "192.168.1.1", "Servers")
        # attention, le fichier dummy.xml doit exister ou l'hôte sera supprimé
        # juste après avoir été inséré
        settings["vigiconf"]["confdir"] = self.tmpdir
        open(os.path.join(self.tmpdir, "dummy.xml"), "w").close() # == touch
        rm = DummyRevMan()
        grouploader = GroupLoader()
        hostloader = HostLoader(grouploader, rm)
        nagios = Nagios()
        vigimap = VigiMap()
        apps = [nagios, vigimap]
        ventilator = get_ventilator(apps)
        loader = LoaderManager(rm)
        loader.load_apps_db(apps)
        hostloader.load()
        loader.load_vigilo_servers_db()

        nb_vigiloservers = DBSession.query(VigiloServer).count()
        self.assertEquals(nb_vigiloservers, 1)

        ventilation = ventilator.ventilate()
        loader.load_ventilation_db(ventilation, apps)
        print DBSession.query(Ventilation).all()
        #
        del conf.appsGroupsByServer["trap"]

        loader.load_vigilo_servers_db()
        # Le nombre de serveurs de supervision ne doit pas bouger.
        nb_vigiloservers = DBSession.query(VigiloServer).count()
        self.assertEquals(nb_vigiloservers, 1)

        ventilation = ventilator.ventilate()
        loader.load_ventilation_db(ventilation, apps)
        print DBSession.query(Ventilation).all()
        trap_app = DBSession.query(Application).filter_by(
                        name=u"snmptt").first()
        trap_ventil = DBSession.query(Ventilation).filter_by(
                        application=trap_app).count()
        self.assertEquals(trap_ventil, 0)


if __name__ == '__main__':
    unittest.main()
