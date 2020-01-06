# -*- coding: utf-8 -*-
# vim:set expandtab tabstop=4 shiftwidth=4:
# Copyright (C) 2006-2020 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Fonctions utilitaires réutilisables dans les différents tests.
"""

import os
import unittest
import vigilo.vigiconf.conf as conf

from vigilo.common.conf import settings

from .helpers import setup_db, teardown_db, DummyRevMan, setup_tmpdir

from vigilo.vigiconf.loaders.group import GroupLoader
from vigilo.vigiconf.loaders.host import HostLoader

from vigilo.models.session import DBSession
from vigilo.models.tables import Host, Graph, PerfDataSource
from vigilo.models.tables.secondary_tables import GRAPH_PERFDATASOURCE_TABLE

from vigilo.vigiconf.lib.confclasses.host import Host as ConfHost


class GraphLoaderTest(unittest.TestCase):

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
        self.revman = DummyRevMan()
        self.grouploader = GroupLoader()


    def tearDown(self):
        teardown_db()


    def test_add_perfdatasource_in_existing_graph(self):
        """Test the addition of perfdatasources in an existing graph"""

        # 1 - Crée un hôte avec un graphe contenant une métrique.

        # Données collectées lors d'un deploy --force
        conf.hostsConf[u'testserver1']['graphItems'] = {u'Load': {
            'last_is_max': False,
            'cdefs': [],
            'template': u'areas',
            'factors': {'Load 01': 0.01},
            'max': None,
            'min': None,
            'ds': [u'Load 01'],
            'vlabel': u'load'}}

        conf.hostsConf[u'testserver1']['dataSources'] = {u'Load 01': {
            'dsType': u'GAUGE',
            'rra_template': None,
            'min': None,
            'label': u'Load 01',
            'max': None}}

        # Chargement des données collectées lors du déploiement
        self.hostloader = HostLoader(self.grouploader, self.revman)
        self.hostloader.load()

        # Nombre de métriques dans la table "vigilo_graphperfdatasource"
        count = DBSession.query(GRAPH_PERFDATASOURCE_TABLE).count()

        # Récupération de la liste de perfdatasource associée au graphe
        g = self.by_graph_and_host_name(u'Load', u'testserver1')
        self.assertNotEqual(g, None)
        self.assertEqual(g.name, u'Load')
        self.assertEqual(count, 1)


        # 2 - Ajoute une deuxième métrique au graphe précédemment créé.
        conf.hostsConf[u'testserver1']['graphItems'][u'Load']['factors'] = \
            {'Load 01': 0.01, 'Load 05': 0.01}
        conf.hostsConf[u'testserver1']['graphItems'][u'Load']['ds'] = \
            [u'Load 01', u'Load 05']

        conf.hostsConf[u'testserver1']['dataSources'][u'Load 05'] = {
            'dsType': 'GAUGE',
            'rra_template': None,
            'min': None,
            'label': u'Load 05',
            'max': None
        }

        self.hostloader = HostLoader(self.grouploader, self.revman)
        self.hostloader.load()

        count2 = DBSession.query(GRAPH_PERFDATASOURCE_TABLE).count()

        g = self.by_graph_and_host_name(u'Load', u'testserver1')
        self.assertNotEqual(g, None)
        self.assertEqual(g.name, u'Load')
        self.assertEqual(count2, 2)


    def by_graph_and_host_name(self, graphname, hostname):
        """
        Renvoie le graphe dont le nom est L{graphname} et appartenant
        à l'hôte L{hostname}.

        @param hostname: Nom de l'hôte possédant le graphe.
        @type  hostname: C{unicode}
        @param graphname: Nom du graphe voulu.
        @type  graphname: C{unicode}
        @return: Le graphe demandé.
        @rtype: L{Graph}
        """
        return DBSession.query(Graph).join(
                    (GRAPH_PERFDATASOURCE_TABLE, \
                        GRAPH_PERFDATASOURCE_TABLE.c.idgraph
                            == Graph.idgraph),
                    (PerfDataSource, PerfDataSource.idperfdatasource == \
                        GRAPH_PERFDATASOURCE_TABLE.c.idperfdatasource),
                    (Host, Host.idhost == \
                        PerfDataSource.idhost),
                ).filter(Graph.name == graphname and Host.name == hostname).first()

