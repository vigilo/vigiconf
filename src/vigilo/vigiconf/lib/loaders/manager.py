# -*- coding: utf-8 -*-
################################################################################
#
# Copyright (C) 2007-2009 CS-SI
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
################################################################################

"""
Ce module contient des fonctions permettant d'exporter dans la base
de données vigilo certaines données de configuration.

* update_apps_db
exporte en base les noms des applications

* export_conf_db
exporte en base les données groupes, les hôtes et les services de bas
niveaux, les groupes de graphes, les services de haut niveau, les
dépendances.

* export_vigilo_servers_DB
exporte en base les données la liste des serveurs de supervision.

* export_ventilation_DB
exporte en base les données la ventilation des hôtes par application
sur les serveurs de supervision.
"""

from __future__ import absolute_import

from pkg_resources import working_set

from vigilo.common.conf import settings
settings.load_module(__name__)

from vigilo.models.session import DBSession


__docformat__ = "epytext"


class LoaderManager(object):
    def __init__(self, dispatchator):
        self.dispatchator = dispatchator

    def load_apps_db(self, apps):
        """mise à jour de la liste des application en base"""
        from vigilo.vigiconf.loaders.application import ApplicationLoader
        apploader = ApplicationLoader(apps)
        apploader.load()
        DBSession.flush()

    def load_conf_db(self):
        """mise à jour de la base de données"""
        # hiérarchie des groupes
        from vigilo.vigiconf.loaders.group import GroupLoader
        grouploader = GroupLoader(self.dispatchator)
        grouploader.load()

        # groupes de graphes
        from vigilo.vigiconf.loaders.graphgroup import GraphGroupLoader
        graphgroup_loader = GraphGroupLoader()
        graphgroup_loader.load()

        # hôtes
        from vigilo.vigiconf.loaders.host import HostLoader
        hostloader = HostLoader(grouploader, self.dispatchator)
        hostloader.load()

        # services de haut niveau
        from vigilo.vigiconf.loaders.hlservice import HLServiceLoader
        hlserviceloader = HLServiceLoader(grouploader, self.dispatchator)
        hlserviceloader.load()

        # dépendances topologiques
        from vigilo.vigiconf.loaders.topology import TopologyLoader
        topologyloader = TopologyLoader(self.dispatchator)
        topologyloader.load()

        DBSession.flush()

        # Loaders spécifiques
        # deux boucles parce qu'on veut forcer le tri des loaders par leur nom
        # dans une distribution donnée. Par défaut, il n'y a pas de tri à
        # l'intérieur d'une même distribution (voir doc de pkg_resources)
        specific_loaders = {}
        for entry in working_set.iter_entry_points("vigilo.vigiconf.loaders"):
            dist = entry.dist.key
            specific_loaders.setdefault(dist, []).append(entry)
        for dist, loaders in specific_loaders.iteritems():
            loaders.sort(cmp=lambda x, y: cmp(x.name, y.name))
            for loader_entry in loaders:
                loadclass = loader_entry.load()
                loader_instance = loadclass()
                loader_instance.load()
                DBSession.flush()

    def load_vigilo_servers_db(self):
        """Export des serveurs de la supervision en base"""
        # serveurs Vigilo
        from vigilo.vigiconf.loaders.vigiloserver import VigiloServerLoader
        vserver_loader = VigiloServerLoader()
        vserver_loader.load()
        DBSession.flush()

    def load_ventilation_db(self, ventilation, apps):
        """Export de la ventilation en base"""
        # ventilation
        from vigilo.vigiconf.loaders.ventilation import VentilationLoader
        ventilationloader = VentilationLoader(ventilation, apps)
        ventilationloader.load()
        DBSession.flush()
