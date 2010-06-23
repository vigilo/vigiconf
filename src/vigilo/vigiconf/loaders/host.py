#!/usr/bin/env python
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

import os

from vigilo.common.conf import settings
from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.models.session import DBSession

from vigilo.models.tables import Host, SupItemGroup, LowLevelService
from vigilo.models.tables import Graph, GraphGroup, PerfDataSource
from vigilo.models.tables import Application, Ventilation, VigiloServer
from vigilo.models.tables import ConfItem
from vigilo.models.tables.secondary_tables import GRAPH_PERFDATASOURCE_TABLE, \
                                                  GRAPH_GROUP_TABLE

from vigilo.vigiconf.lib.dbloader import DBLoader

from vigilo.vigiconf import conf

__docformat__ = "epytext"


class HostLoader(DBLoader):
    """
    Charge les hôtes en base depuis le modèle mémoire.

    Dépend de GroupLoader
    """
    
    def __init__(self):
        super(HostLoader, self).__init__(Host, "name")

    def load_conf(self):
        for hostname, hostdata in conf.hostsConf.iteritems():
            LOGGER.info("Loading host %s", hostname)
            hostname = unicode(hostname)
            host = dict(name=hostname,
                        checkhostcmd=unicode(hostdata['checkHostCMD']),
                        hosttpl=unicode(hostdata['hostTPL']),
                        snmpcommunity=unicode(hostdata['community']),
                        mainip=unicode(hostdata['mainIP']),
                        snmpport=hostdata['port'],
                        snmpoidsperpdu=hostdata['snmpOIDsPerPDU'],
                        weight=hostdata['weight'],
                        snmpversion=unicode(hostdata['snmpVersion']))
            host = self.add(host)
            
            # groupes
            host.groups = []
            for og in hostdata['otherGroups']:
                host.groups.append(SupItemGroup.by_group_name(unicode(og)))
            
            # services
            service_loader = ServiceLoader(host)
            service_loader.load()

            # directives Nagios de l'hôte
            nagiosconf_loader = NagiosConfLoader(host, hostdata['nagiosDirectives'])
            nagiosconf_loader.load()

            # groupes de graphes
            graphgroup_loader = GraphGroupLoader(host)
            graphgroup_loader.load()

            # données de performance
            pds_loader = PDSLoader(host)
            pds_loader.load()

            # graphes
            graph_loader = GraphLoader(host)
            graph_loader.load()

        DBSession.flush()


class ServiceLoader(DBLoader):
    """
    Charge les services en base depuis le modèle mémoire.

    Appelé par le HostLoader
    """
    
    def __init__(self, host):
        super(ServiceLoader, self).__init__(LowLevelService, "servicename")
        self.host = host

    def _list_db(self):
        return DBSession.query(self._class).filter_by(host=self.host).all()

    def load_conf(self):
        # TODO: implémenter les détails: op_dep, weight, command
        for service in conf.hostsConf[self.host.name]['services']:
            service = unicode(service)
            lls = dict(host=self.host, servicename=service,
                       op_dep=u'+', weight=1)
            lls = self.add(lls)
            # directives Nagios du service
            nagios_directives = conf.hostsConf[self.host.name]['nagiosSrvDirs']
            if nagios_directives.has_key(service):
                nagiosconf_loader = NagiosConfLoader(lls, nagios_directives[service])
                nagiosconf_loader.load()


class NagiosConfLoader(DBLoader):
    """
    Charge les directives en base depuis le modèle mémoire.

    Appelé par le HostLoader. Peut fonctionner pour des hôtes ou des services,
    et dépend du loader correspondant.
    """
    
    def __init__(self, supitem, directives):
        # On ne travaille que sur les directives d'un seul supitem à la fois,
        # la clé "name" est donc unique
        super(NagiosConfLoader, self).__init__(ConfItem, "name")
        self.supitem = supitem
        self.directives = directives

    def _list_db(self):
        return DBSession.query(self._class).filter_by(supitem=self.supitem).all()

    def load_conf(self):
        for name, value in self.directives.iteritems():
            name = unicode(name)
            value = unicode(value)
            ci = dict(supitem=self.supitem, name=name, value=value)
            self.add(ci)


class PDSLoader(DBLoader):
    """
    Charge les sources de données de performance en base depuis le modèle
    mémoire.

    Appelé par le HostLoader
    """
    
    def __init__(self, host):
        # On ne travaille que sur les directives d'un seul host à la fois,
        # la clé "name" est donc unique
        super(PDSLoader, self).__init__(PerfDataSource, "name")
        self.host = host

    def _list_db(self):
        return DBSession.query(self._class).filter_by(host=self.host).all()

    def load_conf(self):
        datasources = conf.hostsConf[self.host.name]['dataSources']
        for dsname, dsdata in datasources.iteritems():
            pds = dict(host=self.host, name=unicode(dsname),
                       type=unicode(dsdata["dsType"]),
                       label=unicode(dsdata['label']))
            for graphname, graphdata in conf.hostsConf[self.host.name]['graphItems'].iteritems():
                if graphdata['factors'].has_key(dsname):
                    pds["factor"] = float(graphdata['factors'][dsname])
            self.add(pds)


class GraphGroupLoader(DBLoader):
    """
    Charge les groupes de graphes en base depuis le modèle mémoire.

    Appelé par le HostLoader
    """
    
    def __init__(self, host):
        super(GraphGroupLoader, self).__init__(GraphGroup, "name")
        self.host = host

    def load(self):
        self.load_conf()
        # Pas de cleanup, c'est fait par le GraphLoader
        DBSession.flush()

    def load_conf(self):
        for groupname in conf.hostsConf[self.host.name]['graphGroups']:
            groupname = unicode(groupname)
            if not GraphGroup.by_group_name(groupname):
                group = GraphGroup(name=groupname)
                DBSession.add(group)


class GraphLoader(DBLoader):
    """
    Charge les graphes en base depuis le modèle mémoire.

    Appelé par le HostLoader, dépend de PDSLoader et de GraphGroupLoader
    """
    
    def __init__(self, host):
        super(GraphLoader, self).__init__(Graph, "name")
        self.host = host

    def _list_db(self):
        """Charge toutes les instances depuis la base de données"""
        return DBSession.query(self._class).join(
                        (GRAPH_PERFDATASOURCE_TABLE, \
                            GRAPH_PERFDATASOURCE_TABLE.c.idgraph == Graph.idgraph),
                        (PerfDataSource, PerfDataSource.idperfdatasource == \
                            GRAPH_PERFDATASOURCE_TABLE.c.idperfdatasource),
                    ).filter(PerfDataSource.host == self.host).all()

    def load_conf(self):
        for graphname, graphdata in conf.hostsConf[self.host.name]['graphItems'].iteritems():
            graphname = unicode(graphname)
            graph = dict(name=graphname,
                         template=unicode(graphdata['template']),
                         vlabel=unicode(graphdata["vlabel"]),
                        )
            graph = self.add(graph)
            # lien avec les PerfDataSources
            graph.perfdatasources = []
            for dsname in graphdata['ds']:
                pds = PerfDataSource.by_host_and_source_name(self.host, unicode(dsname))
                graph.perfdatasources.append(pds)
            # lien avec les GraphGroups
            graph.groups = []
            for groupname, graphnames in conf.hostsConf[self.host.name]['graphGroups'].iteritems():
                if graphname not in graphnames:
                    continue
                group = GraphGroup.by_group_name(groupname)
                graph.groups.append(group)

    def cleanup(self):
        """
        En plus du cleanup normal, on supprime les graphes et les groupes de
        graphes vides
        """
        super(GraphLoader, self).cleanup()
        for graph in DBSession.query(Graph):
            if not graph.perfdatasources:
                DBSession.delete(graph)
        for group in DBSession.query(GraphGroup):
            if not group.graphs:
                DBSession.delete(group)


