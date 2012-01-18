# -*- coding: utf-8 -*-
################################################################################
#
# Copyright (C) 2007-2011 CS-SI
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

from sqlalchemy import or_

from vigilo.common.conf import settings
from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

from vigilo.models.session import DBSession

from vigilo.models.tables import Host, SupItemGroup, LowLevelService
from vigilo.models.tables import Graph, GraphGroup, PerfDataSource
from vigilo.models.tables import ConfFile, ConfItem, Change, Tag
from vigilo.models.tables import SupItem, HighLevelService, GroupPath
from vigilo.models.tables import MapLink, MapServiceLink, MapSegment
from vigilo.models.tables import MapNode, MapNodeHost, MapNodeService
from vigilo.models.tables.group import Group
from vigilo.models.tables.secondary_tables import GRAPH_PERFDATASOURCE_TABLE

from vigilo.vigiconf.lib.loaders import DBLoader
from vigilo.vigiconf.lib import ParsingError
from vigilo.vigiconf import conf
from vigilo.common import parse_path

__docformat__ = "epytext"


class HostLoader(DBLoader):
    """
    Charge les hôtes en base depuis le modèle mémoire.

    Dépend de GroupLoader
    """

    def __init__(self, grouploader, rev_mgr):
        super(HostLoader, self).__init__(Host, "name")
        self.grouploader = grouploader
        self.rev_mgr = rev_mgr
        self.conffiles = dict()
        self.group_cache = dict()
        self.group_parts_cache = dict()

    def cleanup(self):
        # Presque rien à faire ici : la fin du load_conf se charge déjà
        # de supprimer les instances de ConfFile retirées du SVN,
        # ce qui a pour effet de supprimer les hôtes associés.
        # Elle supprime aussi les hôtes qui n'ont pas de fichier
        # attaché (résidus laissés lors de la migration vers ConfFile).
        # Il reste uniquement à vérifier qu'on a pas encore en base des
        # fichiers qui auraient disparu du disque (modif SVN manuelle par
        # exemple)
        LOGGER.debug("Checking for leftover ConfFiles")
        for conffilename in self.conffiles:
            # self.conffiles indexe les objets par leur ID, mais aussi
            # pas leur nom de fichier, on ne s'intéresse qu'à ces derniers.
            if not isinstance(conffilename, basestring):
                continue

            filename = os.path.join(settings["vigiconf"].get("confdir"),
                                    conffilename)
            if not os.path.exists(filename):
                LOGGER.warning(_("Deleting leftover config file from "
                                 "database: %s"), conffilename)
                DBSession.delete(self.conffiles[conffilename])
        DBSession.flush()

    def load_conf(self):
        LOGGER.info(_("Loading hosts"))
        # On récupère d'abord la liste de tous les hôtes
        # précédemment définis en base et le fichier XML
        # auquels ils appartiennent.
        previous_hosts = {}

        for conffile in DBSession.query(ConfFile).all():
            self.conffiles[conffile.idconffile] = conffile
            self.conffiles[conffile.name] = conffile

        db_hosts = DBSession.query(
                Host.name,
                Host.idconffile,
            ).all()
        for db_host in db_hosts:
            previous_hosts[db_host.name] = self.conffiles[db_host.idconffile]

        hostnames = []
        # On ne s'interresse qu'à ceux sur lesquels une modification
        # a eu lieu (ajout ou modification). On génère en même temps
        # un cache des instances des fichiers de configuration.
        for hostname in conf.hostsConf.keys():
            filename = conf.hostsConf[hostname]["filename"]
            relfilename = filename[len(settings["vigiconf"].get("confdir"))+1:]

            if self.rev_mgr.file_changed(filename, exclude_removed=True):
                hostnames.append(hostname)

            # Peuple le cache en créant les instances à la volée si
            # nécessaire.
            if relfilename not in self.conffiles:
                LOGGER.debug(_("Registering new configuration file "
                                "'%(relative)s' (from %(absolute)s)"), {
                                    'relative': relfilename,
                                    'absolute': filename,
                                })
                conffile = ConfFile(name=unicode(relfilename))
                DBSession.flush()
                self.conffiles[unicode(relfilename)] = conffile
                self.conffiles[conffile.idconffile] = conffile

        # Utile pendant la migration des données :
        # les hôtes pour lesquels on ne possédait pas d'informations
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
            relfilename = hostdata['filename'] \
                [len(settings["vigiconf"].get("confdir"))+1:]
            LOGGER.debug(_("Loading host %s"), hostname)
            hostname = unicode(hostname)
            host = dict(name=hostname,
                        hosttpl=unicode(hostdata['hostTPL']),
                        snmpcommunity=unicode(hostdata['snmpCommunity']),
                        address=unicode(hostdata['address']),
                        snmpport=hostdata['snmpPort'],
                        snmpoidsperpdu=hostdata['snmpOIDsPerPDU'],
                        weight=hostdata['weight'],
                        snmpversion=unicode(hostdata['snmpVersion']),
                        conffile=self.conffiles[unicode(relfilename)],
                    )
            host = self.add(host)
            hosts[hostname] = host

            # Synchronise le service "Collector"
            # en fonction des besoins.
            collector_loader = CollectorLoader(host)
            collector_loader.load()

            # Synchronisation des tags de l'hôte.
            tag_loader = TagLoader(host, hostdata.get('tags', {}))
            tag_loader.load()

        if hostnames:
            LOGGER.debug("Preparing group cache")
            groups = DBSession.query(GroupPath).join(
                    (Group, Group.idgroup == GroupPath.idgroup)
                ).filter(Group._grouptype == u'supitemgroup').all()
            for g in groups:
                self.group_cache[g.idgroup] = g.path
                self.group_cache[g.path] = g.idgroup
                for part in parse_path(g.path):
                    self.group_parts_cache.setdefault(part, []).append(g.path)

        for hostname in hostnames:
            hostdata = conf.hostsConf[hostname]
            host = hosts[hostname]

            # groupes
            LOGGER.debug("Loading groups for host %s", hostname)
            self._load_groups(host, hostdata)

            # services
            LOGGER.debug("Loading services for host %s", hostname)
            service_loader = ServiceLoader(host)
            service_loader.load()

            # directives Nagios de l'hôte
            LOGGER.debug("Loading nagios conf for host %s", hostname)
            nagiosconf_loader = NagiosConfLoader(host,
                                    hostdata['nagiosDirectives'])
            nagiosconf_loader.load()

            # données de performance
            LOGGER.debug("Loading perfdatasources for host %s", hostname)
            pds_loader = PDSLoader(host)
            pds_loader.load()

            # graphes
            LOGGER.debug("Loading graphs for host %s", hostname)
            graph_loader = GraphLoader(host)
            graph_loader.load()

        # Suppression des fichiers de configuration retirés du SVN
        # ainsi que de leurs hôtes (par CASCADE).
        LOGGER.debug("Cleaning up old hosts")
        removed = self.rev_mgr.get_removed()
        for filename in removed:
            relfilename = filename[len(settings["vigiconf"].get("confdir"))+1:]
            # si un dossier est supprimé avec rm -rf, SVN ne signale que le
            # dossier, pas tous ses fichiers/sous-dossiers -> on doit utiliser
            # un LIKE pour les attrapper
            DBSession.query(ConfFile).filter(or_(
                    ConfFile.name == unicode(relfilename),
                    ConfFile.name.like(unicode(relfilename) + u"/%")
                )).delete()
        LOGGER.debug("Done cleaning up old hosts")

        # Ghostbusters
        # 1- Hosts qui n'ont plus de fichier de configuration.
        ghost_hosts = DBSession.query(Host.idhost).filter(
                        Host.idconffile == None).all()
        nb_ghosts = DBSession.query(SupItem).filter(
                SupItem.idsupitem.in_([ h.idhost for h in ghost_hosts ])
            ).delete()
        LOGGER.debug("Deleted %d ghosts [Host]", nb_ghosts)

        # 2- SupItems qui ne sont ni des hôtes, ni des HLS/LLS.
        ghost_hosts = DBSession.query(Host.idhost.label('idsupitem'))
        ghost_lls = DBSession.query(LowLevelService.idservice.label(
                                    'idsupitem'))
        ghost_hls = DBSession.query(HighLevelService.idservice.label(
                                    'idsupitem'))
        union = ghost_hosts.union(ghost_lls).union(ghost_hls).subquery()
        ghost_all = DBSession.query(SupItem.idsupitem).outerjoin(
                (union, union.c.idsupitem == SupItem.idsupitem)
            ).filter(union.c.idsupitem == None).all()
        nb_ghosts = DBSession.query(SupItem).filter(
                    SupItem.idsupitem.in_([ s.idsupitem for s in ghost_all ])
                ).delete()
        LOGGER.debug("Deleted %d ghosts [SupItem]", nb_ghosts)

        # 3- MapLinks qui n'ont pas de type (lien service ou segment).
        service_link = DBSession.query(MapServiceLink.idmapservicelink.label(
                                       'idmaplink'))
        segment = DBSession.query(MapSegment.idmapsegment.label('idmaplink'))
        union = service_link.union(segment).subquery()
        ghost_all = DBSession.query(MapLink.idmaplink).outerjoin(
                (union, union.c.idmaplink == MapLink.idmaplink)
            ).filter(union.c.idmaplink == None).all()
        nb_ghosts = DBSession.query(MapLink).filter(
                MapLink.idmaplink.in_([ ml.idmaplink for ml in ghost_all ])
            ).delete()
        LOGGER.debug("Deleted %d ghosts [MapLink]", nb_ghosts)

        # 4- MapNodes qui n'ont pas d'entité (hôte/HLS/LLS) associée.
        node_host = DBSession.query(MapNodeHost.idmapnode.label('idmapnode'))
        node_service = DBSession.query(MapNodeService.idmapnode.label(
                                       'idmapnode'))
        union = node_host.union(node_service).subquery()
        ghost_all = DBSession.query(MapNode.idmapnode).outerjoin(
                (union, union.c.idmapnode == MapNode.idmapnode)
            ).filter(union.c.idmapnode == None
            ).filter(MapNode.type_node != None).all()
        nb_ghosts = DBSession.query(MapNode).filter(
                MapNode.idmapnode.in_([ mn.idmapnode for mn in ghost_all ])
            ).delete()
        LOGGER.debug("Deleted %d ghosts [MapNode]", nb_ghosts)

        # Suppression des hôtes qui ont été supprimés dans les fichiers
        # modifiés
        deleted_hosts = []
        for conffilename in self.conffiles:
            if not isinstance(conffilename, basestring):
                continue
            filename = os.path.join(settings["vigiconf"].get("confdir"),
                                    conffilename)
            if not self.rev_mgr.file_changed(filename):
                continue # ce fichier n'a pas bougé
            for host in self.conffiles[conffilename].hosts:
                if host.name not in hostnames:
                    LOGGER.debug("Deleting '%s'", host.name)
                    deleted_hosts.append(host)
                    DBSession.delete(host)

        # Nettoyage des graphes et des groupes de graphes vides
        LOGGER.debug("Cleaning up old graphs and graphgroups")
        empty_graphs = DBSession.query(Graph).distinct().filter(
                            ~Graph.perfdatasources.any()).all()
        for graph in empty_graphs:
            DBSession.delete(graph)

        # Si on a changé quelquechose, on le note en base
        if hostnames or removed or ghost_hosts or deleted_hosts \
                or empty_graphs:
            Change.mark_as_modified(u"Host")
            Change.mark_as_modified(u"Service")
            Change.mark_as_modified(u"Graph")

        DBSession.flush()
        LOGGER.info(_("Done loading hosts"))

    def _absolutize_groups(self, host, hostdata):
        """Transformation des chemins relatifs en chemins absolus."""
        old_groups = hostdata['otherGroups'].copy()
        hostdata["otherGroups"] = set()

        for old_group in old_groups:
            if old_group.startswith('/'):
                hostdata["otherGroups"].add(old_group)
                continue

            groups = self.group_parts_cache.get(old_group)
            if not groups:
                raise ParsingError(_('Unknown group "%(group)s" in host '
                                     '"%(host)s".')
                                   % {"group": old_group, "host": host.name})
            hostdata["otherGroups"].update(groups)

    def _load_groups(self, host, hostdata):
        self._absolutize_groups(host, hostdata)

        # Rempli à mesure que des groupes sont ajoutés (sorte de cache).
        hostgroups_cache = {}
        for g in host.groups:
            hostgroups_cache[g.idgroup] = g

        # Suppression des anciens groupes
        # qui ne sont plus associés à l'hôte.
        for idgroup in hostgroups_cache.copy():
            path = self.group_cache[idgroup]
            if path not in hostdata['otherGroups']:
                host.groups.remove(hostgroups_cache[idgroup])
                del hostgroups_cache[idgroup]

        # Ajout des nouveaux groupes associés à l'hôte.
        hierarchy = self.grouploader.get_hierarchy()
        for path in hostdata['otherGroups']:
            if path not in self.group_cache:
                msg = _("syntax error in host %(host)s: could not find a group "
                        "matching path \"%(path)s\"")
                raise ParsingError(msg % {
                    'host': host.name,
                    'path': path,
                })

            idgroup = self.group_cache[path]
            if idgroup in hostgroups_cache:
                continue

            if path not in hierarchy:
                msg = _("syntax error in host %(host)s: could not find a group "
                        "matching path \"%(path)s\"")
                raise ParsingError(msg % {
                    'host': host.name,
                    'path': path,
                })

            host.groups.append(hierarchy[path])
            hostgroups_cache[idgroup] = hierarchy[path]

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
        #return [ s for s in DBSession.query(self._class).filter_by(
        #         host=self.host).all() if s.servicename != 'Collector' ]

    def load_conf(self):
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
            warning_weight = conf.hostsConf[self.host.name]['services'] \
                [service]['warning_weight']
            lls = dict(host=self.host, servicename=service,
                       weight=weight, warning_weight=warning_weight,
                       idcollector=idcollector)
            lls = self.add(lls)

            # directives Nagios du service
            nagios_directives = conf.hostsConf[self.host.name]['nagiosSrvDirs']
            if nagios_directives.has_key(service):
                nagiosconf_loader = NagiosConfLoader(lls,
                                        nagios_directives[service])
                nagiosconf_loader.load()

            # tags
            if service in conf.hostsConf[self.host.name]['services']:
                tag_loader = TagLoader(lls, conf.hostsConf[self.host.name] \
                    ['services'][service].get('tags', {}))
                tag_loader.load_conf()

class CollectorLoader(ServiceLoader):
    def _list_db(self):
        return DBSession.query(self._class).filter_by(host=self.host
            ).filter(self._class.servicename == u'Collector').all()

    def load_conf(self):
        hostdata = conf.hostsConf[self.host.name]
        if "SNMPJobs" in hostdata and hostdata['SNMPJobs']:
            LOGGER.debug('Adding "Collector" service on host %s',
                         self.host.name)
            lls = dict(host=self.host, servicename=u"Collector",
                        weight=1, warning_weight=1)
            lls = self.add(lls)

            # tags
            if 'Collector' in hostdata['services']:
                tag_loader = TagLoader(lls, hostdata['services'] \
                    ['Collector'].get('tags', {}))
                tag_loader.load_conf()


class TagLoader(DBLoader):
    """Chargeur de tags. Attention les valeurs des tags sont ignorées"""

    all_tags = {}

    def __init__(self, supitem, tags):
        super(TagLoader, self).__init__(Tag, "name")
        self.supitem = supitem
        self.tags = tags

    def cleanup(self):
        pass

    def load_conf(self):
        self.supitem.tags = self.tags

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
        return DBSession.query(self._class).filter_by(
                    supitem=self.supitem).all()

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
            if "max" in dsdata and dsdata["max"] is not None:
                pds["max"] = float(dsdata["max"])
            for graphdata in conf.hostsConf[self.host.name]\
                                                ['graphItems'].values():
                if graphdata['factors'].get(dsname, None) is not None:
                    pds["factor"] = float(graphdata['factors'][dsname])
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
                            GRAPH_PERFDATASOURCE_TABLE.c.idgraph
                                == Graph.idgraph),
                        (PerfDataSource, PerfDataSource.idperfdatasource == \
                            GRAPH_PERFDATASOURCE_TABLE.c.idperfdatasource),
                    ).filter(PerfDataSource.idhost == self.host.idhost).all()

    def load_conf(self):
        # lecture du modèle mémoire
        for graphname, graphdata in conf.hostsConf[self.host.name]\
                                            ['graphItems'].iteritems():
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
            pds = PerfDataSource.by_host_and_source_name(self.host.idhost,
                                                         unicode(dsname))
            graph.perfdatasources.append(pds)
        # lien avec les GraphGroups
        for groupname, graphnames in conf.hostsConf[self.host.name]\
                                                ['graphGroups'].iteritems():
            if graphname not in graphnames:
                continue
            group = GraphGroup.by_group_name(groupname)
            graph.groups.append(group)
