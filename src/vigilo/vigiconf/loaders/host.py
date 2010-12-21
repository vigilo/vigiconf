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

from vigilo.common.gettext import translate
_ = translate(__name__)

from vigilo.models.session import DBSession

from vigilo.models.tables import Host, SupItemGroup, LowLevelService
from vigilo.models.tables import Graph, GraphGroup, PerfDataSource
from vigilo.models.tables import Application, Ventilation, VigiloServer
from vigilo.models.tables import ConfFile, ConfItem
from vigilo.models.tables.secondary_tables import GRAPH_PERFDATASOURCE_TABLE, \
                                                  GRAPH_GROUP_TABLE

from vigilo.vigiconf.lib.loaders import DBLoader
from vigilo.vigiconf.lib.confclasses import parse_path
from vigilo.vigiconf.lib import ParsingError
from vigilo.vigiconf.lib.revisionmanager import RevisionManager

from vigilo.vigiconf import conf

__docformat__ = "epytext"


class HostLoader(DBLoader):
    """
    Charge les hôtes en base depuis le modèle mémoire.

    Dépend de GroupLoader
    """

    def __init__(self, grouploader, dispatchator):
        super(HostLoader, self).__init__(Host, "name")
        self.grouploader = grouploader
        self.dispatchator = dispatchator

    def cleanup(self):
        # Rien à faire ici : la fin du load_conf se charge déjà
        # de supprimer les instances de ConfFile retirées du SVN,
        # ce qui a pour effet de supprimer les hôtes associés.
        # Elle supprime aussi les hôtes qui n'ont pas de fichier
        # attaché (résidus laissés lors de la migration vers ConfFile).
        pass

    def load_conf(self):
        # On récupère d'abord la liste de tous les hôtes
        # précédemment définis en base et le fichier XML
        # auquels ils appartiennent.
        previous_hosts = {}
        db_hosts = DBSession.query(
                Host.name,
                ConfFile.name.label('conffile')
            ).outerjoin(
                (ConfFile, Host.idconffile == ConfFile.idconffile),
            ).all()
        for db_host in db_hosts:
            previous_hosts[db_host.name] = db_host.conffile

        hostnames = []
        conffiles = {}
        svn_status = self.dispatchator.get_svn_status()

        # On ne s'interresse qu'à ceux sur lesquels une modification
        # a eu lieu (ajout ou modification). On génère en même temps
        # un cache des instances des fichiers de configuration.
        for hostname in conf.hostsConf.keys():
            filename = conf.hostsConf[hostname]["filename"]
            relfilename = filename[len(settings["vigiconf"].get("confdir"))+1:]

            # On ajoute systématiquement le nom du fichier dans la liste
            # de ceux à traiter si l'option "--force" a été utilisée.
            if self.dispatchator.getModeForce() or \
                filename in svn_status['add'] or \
                filename in svn_status['modified']:
                hostnames.append(hostname)

            # Peuple le cache en créant les instances à la volée si nécessaire.
            conffiles.setdefault(filename, ConfFile.get_or_create(relfilename))

        # Utile pendant la migration des données :
        # les hôtes pour lesquels on ne possèdait pas d'informations
        # quant au fichier de définition doivent être mis à jour.
        for hostname, conffile in previous_hosts.iteritems():
            if conffile is None:
                hostnames.append(hostname)
        del previous_hosts

        # Fera office de cache des instances d'hôtes
        # entre les deux étapes de la synchronisation.
        hosts = {}

        hostnames = sorted(list(set(hostnames)))
        for hostname in hostnames:
            hostdata = conf.hostsConf[hostname]
            LOGGER.info(_("Loading host %s"), hostname)
            hostname = unicode(hostname)
            host = dict(name=hostname,
                        checkhostcmd=unicode(hostdata['checkHostCMD']),
                        hosttpl=unicode(hostdata['hostTPL']),
                        snmpcommunity=unicode(hostdata['community']),
                        address=unicode(hostdata['address']),
                        snmpport=hostdata['snmpPort'],
                        snmpoidsperpdu=hostdata['snmpOIDsPerPDU'],
                        weight=hostdata['weight'],
                        snmpversion=unicode(hostdata['snmpVersion']),
                        conffile=conffiles[unicode(hostdata['filename'])],
                    )
            host = self.add(host)
            hosts[hostname] = host

            # Synchronise le service "Collector"
            # en fonction des besoins.
            collector_loader = CollectorLoader(host)
            collector_loader.load()

        for hostname in hostnames:
            hostdata = conf.hostsConf[hostname]
            host = hosts[hostname]

            # groupes
            LOGGER.debug(_("Loading groups for host %s"), hostname)
            self._load_groups(host, hostdata)

            # services
            LOGGER.debug(_("Loading services for host %s"), hostname)
            service_loader = ServiceLoader(host)
            service_loader.load()

            # directives Nagios de l'hôte
            LOGGER.debug(_("Loading nagios conf for host %s"), hostname)
            nagiosconf_loader = NagiosConfLoader(host, hostdata['nagiosDirectives'])
            nagiosconf_loader.load()

            # données de performance
            LOGGER.debug(_("Loading perfdatasources for host %s"), hostname)
            pds_loader = PDSLoader(host)
            pds_loader.load()

            # graphes
            LOGGER.debug(_("Loading graphs for host %s"), hostname)
            graph_loader = GraphLoader(host)
            graph_loader.load()

        # Suppression des fichiers de configuration retirés du SVN
        # ainsi que de leurs hôtes (par CASCADE).
        LOGGER.debug(_("Cleaning up old hosts"))
        for filename in svn_status['remove']:
            relfilename = filename[len(settings["vigiconf"].get("confdir"))+1:]
            DBSession.query(ConfFile).filter(
                ConfFile.name == relfilename).delete()

        # Suppression des instances d'hôtes qui n'ont pas de
        # fichier de configuration associé (résidus après migrations).
        ghost_hosts = DBSession.query(Host).filter(
                        Host.idconffile == None).all()
        for host in ghost_hosts:
            LOGGER.debug(_("Removing ghost host '%s'"), host.name)
            DBSession.delete(host)

        # Nettoyage des graphes et les groupes de graphes vides
        LOGGER.debug(_("Cleaning up old graphs and graphgroups"))
        empty_graphs = DBSession.query(Graph).distinct().filter(
                            ~Graph.perfdatasources.any()).all()
        for graph in empty_graphs:
            DBSession.delete(graph)

        DBSession.flush()

    def _absolutize_groups(self, host, hostdata):
        """Transformation des chemins relatifs en chemins absolus."""
        old_groups = hostdata['otherGroups'].copy()
        hostdata["otherGroups"] = set()
        for old_group in old_groups:
            if old_group.startswith('/'):
                hostdata["otherGroups"].add(old_group)
                continue
            groups = DBSession.query(
                            SupItemGroup
                        ).filter(SupItemGroup.name == old_group
                        ).all()
            if not groups:
                raise ParsingError(_('Unknown group "%(group)s" in host "%(host)s".')
                                  % {"group": old_group, "host": host.name})
            for group in groups:
                hostdata["otherGroups"].add(group.path)

    def _load_groups(self, host, hostdata):
        self._absolutize_groups(host, hostdata)
        # Rempli à mesure que des groupes sont ajoutés (sorte de cache).
        hostgroups_cache = {}
        for g in host.groups:
            hostgroups_cache[g.path] = g

        # Suppression des anciens groupes
        # qui ne sont plus associés à l'hôte.
        for path in hostgroups_cache.copy():
            if path not in hostdata['otherGroups']:
                host.groups.remove(hostgroups_cache[path])
                del hostgroups_cache[path]

        # Ajout des nouveaux groupes associés à l'hôte.
        hierarchy = self.grouploader.get_hierarchy()
        for path in hostdata['otherGroups']:
            if path in hostgroups_cache:
                continue

            if path not in hierarchy:
                msg = _("syntax error in host %(host)s: could not find a group "
                        "matching path \"%(path)s\"")
                raise ParsingError(msg % {
                    'host': host.name,
                    'path': path,
                })

            host.groups.append(hierarchy[path])
            hostgroups_cache[path] = hierarchy[path]

class ServiceLoader(DBLoader):
    """
    Charge les services en base depuis le modèle mémoire.

    Appelé par le HostLoader
    """

    def __init__(self, host):
        super(ServiceLoader, self).__init__(LowLevelService, "servicename")
        self.host = host

    def _list_db(self):
        return DBSession.query(self._class).filter_by(host=self.host
            ).filter(self._class.servicename != u'Collector').all()

    def load_conf(self):
        # TODO: implémenter les détails: weight, command
        for service in conf.hostsConf[self.host.name]['services']:
            idcollector = None

            # L'hôte héberge un Collector, on récupère l'ID du Collector.
            if (service, 'service') in \
                conf.hostsConf[self.host.name]['SNMPJobs']:
                idcollector = LowLevelService.get_supitem(
                    self.host.name, u'Collector')

            # L'hôte est rerouté, on récupère l'ID du service de reroutage.
            elif conf.hostsConf[self.host.name]['services'] \
                [service]['reRoutedBy']:
                reRoutedBy = conf.hostsConf[self.host.name]['services'] \
                    [service]['reRoutedBy']
                idcollector = LowLevelService.get_supitem(
                    reRoutedBy['host'], reRoutedBy['service'])

            service = unicode(service)
            weight = conf.hostsConf[self.host.name]['services'] \
                [service]['weight']
            lls = dict(host=self.host, servicename=service,
                       weight=weight, idcollector=idcollector)
            lls = self.add(lls)

            # directives Nagios du service
            nagios_directives = conf.hostsConf[self.host.name]['nagiosSrvDirs']
            if nagios_directives.has_key(service):
                nagiosconf_loader = NagiosConfLoader(lls, nagios_directives[service])
                nagiosconf_loader.load()

class CollectorLoader(ServiceLoader):
    def _list_db(self):
        return DBSession.query(self._class).filter_by(host=self.host
            ).filter(self._class.servicename == u'Collector').all()

    def load_conf(self):
        hostdata = conf.hostsConf[self.host.name]
        if hostdata['services'] and hostdata['SNMPJobs']:
            LOGGER.info(
                _('Adding "Collector" service on host %s'),
                self.host.name
            )
            lls = dict(host=self.host, servicename=u"Collector", weight=1)
            lls = self.add(lls)

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
            pds = dict(idhost=self.host.idhost, name=unicode(dsname),
                       type=unicode(dsdata["dsType"]),
                       label=unicode(dsdata['label']))
            for graphname, graphdata in conf.hostsConf[self.host.name]['graphItems'].iteritems():
                if graphdata['factors'].get(dsname, None) is not None:
                    pds["factor"] = float(graphdata['factors'][dsname])
                if graphdata['max_values'].get(dsname, None) is not None:
                    pds["max"] = float(graphdata['max_values'][dsname])
            self.add(pds)


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
        # lecture du modèle mémoire
        for graphname, graphdata in conf.hostsConf[self.host.name]['graphItems'].iteritems():
            graphname = unicode(graphname)
            graph = dict(name=graphname,
                         template=unicode(graphdata['template']),
                         vlabel=unicode(graphdata["vlabel"]),
                        )
            graph = self.add(graph)

    def insert(self, data):
        """
        En plus de l'ajout classique, on règle les PerfDataSources et les
        GraphGroups
        """
        graph = super(GraphLoader, self).insert(data)
        graphname = data["name"]
        graphdata = conf.hostsConf[self.host.name]['graphItems'][graphname]
        # lien avec les PerfDataSources
        for dsname in graphdata['ds']:
            pds = PerfDataSource.by_host_and_source_name(self.host, unicode(dsname))
            graph.perfdatasources.append(pds)
        # lien avec les GraphGroups
        for groupname, graphnames in conf.hostsConf[self.host.name]['graphGroups'].iteritems():
            if graphname not in graphnames:
                continue
            group = GraphGroup.by_group_name(groupname)
            graph.groups.append(group)
