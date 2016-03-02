# -*- coding: utf-8 -*-
################################################################################
#
# Copyright (C) 2007-2016 CS-SI
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
from vigilo.models.tables import MapLlsLink, MapHlsLink, MapNodeLls, MapNodeHls
from vigilo.models.tables import MapNode, MapNodeHost, MapNodeService
from vigilo.models.tables.group import Group
from vigilo.models.tables.supitemgroup2supitem import SupItemGroup2SupItem
from vigilo.models.tables.secondary_tables import GRAPH_PERFDATASOURCE_TABLE, \
                                                    SUPITEM_GROUP_TABLE

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
                        snmpversion=unicode(hostdata['snmpVersion']),
                        conffile=self.conffiles[unicode(relfilename)],
                    )
            host = self.add(host)
            hosts[hostname] = host

            # Synchronisation des tags de l'hôte.
            tag_loader = TagLoader(host, hostdata.get('tags', {}))
            tag_loader.load()

        if hostnames:
            LOGGER.debug("Preparing group cache")
            groups = DBSession.query(GroupPath).join(
                    (Group, Group.idgroup == GroupPath.idgroup)
                ).filter(Group.grouptype == u'supitemgroup').all()
            for g in groups:
                self.group_cache[g.idgroup] = g.path
                self.group_cache[g.path] = g.idgroup
                for part in parse_path(g.path):
                    self.group_parts_cache.setdefault(part, []).append(g.path)

        # Cache de l'association entre le nom d'un groupe de graphes
        # et son identifiant.
        graphgroups = {}
        for graphgroup in DBSession.query(GraphGroup).all():
            graphgroups[graphgroup.name] = graphgroup

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

            # données de performance
            LOGGER.debug("Loading perfdatasources for host %s", hostname)
            pds_loader = PDSLoader(host)
            pds_loader.load()

            # graphes
            LOGGER.debug("Loading graphs for host %s", hostname)
            graph_loader = GraphLoader(host, graphgroups)
            graph_loader.load()

        # Suppression des fichiers de configuration retirés du SVN
        # ainsi que de leurs hôtes (par CASCADE).
        LOGGER.debug("Cleaning up old hosts")
        removed = self.rev_mgr.get_removed()
        for filename in removed:
            relfilename = filename[len(settings["vigiconf"].get("confdir"))+1:]
            # Si un dossier est supprimé avec rm -rf, SVN ne signale que le
            # dossier, pas tous ses fichiers/sous-dossiers -> on doit utiliser
            # un LIKE pour les attrapper
            DBSession.query(ConfFile).filter(or_(
                    ConfFile.name == unicode(relfilename),
                    ConfFile.name.like(unicode(relfilename) + u"/%")
                )).delete(synchronize_session='fetch')
        LOGGER.debug("Done cleaning up old hosts")

        # Ghostbusters
        # 1- Hosts qui n'ont plus de fichier de configuration.
        nb_ghosts = DBSession.query(
                SupItem.__table__
            ).filter(
                SupItem.__table__.c.idsupitem.in_(
                    DBSession.query(
                        Host.__table__.c.idhost
                    ).filter(Host.__table__.c.idconffile == None)
                )
            ).delete(synchronize_session=False)
        LOGGER.debug("Deleted %d ghosts [Host]", nb_ghosts)


        # 2a- SupItems censés être des hôtes, mais qui n'ont pas d'entrée
        #     dans la table Host.
        nb_ghosts = DBSession.query(
                SupItem.__table__
            ).filter(
                SupItem.__table__.c.idsupitem.in_(
                    DBSession.query(
                        SupItem.idsupitem
                    ).outerjoin(
                        (Host.__table__,
                            Host.__table__.c.idhost ==
                            SupItem.__table__.c.idsupitem)
                    ).filter(
                        SupItem.__table__.c.itemtype ==
                            Host.__mapper_args__['polymorphic_identity']
                    ).filter(Host.__table__.c.idhost == None)
                )
            ).delete(synchronize_session=False)

        # 2b- SupItems censés être des LLS, mais qui n'ont pas d'entrée
        #     dans la table LowLevelService.
        nb_ghosts += DBSession.query(
                SupItem.__table__
            ).filter(
                SupItem.__table__.c.idsupitem.in_(
                    DBSession.query(
                        SupItem.idsupitem
                    ).outerjoin(
                        (LowLevelService.__table__,
                            LowLevelService.__table__.c.idservice ==
                            SupItem.__table__.c.idsupitem)
                    ).filter(
                        SupItem.__table__.c.itemtype ==
                        LowLevelService.__mapper_args__['polymorphic_identity']
                    ).filter(LowLevelService.__table__.c.idservice == None)
                )
            ).delete(synchronize_session=False)

        # 2c- SupItems censés être des HLS, mais qui n'ont pas d'entrée
        #     dans la table HighLevelService.
        nb_ghosts += DBSession.query(
                SupItem.__table__
            ).filter(
                SupItem.__table__.c.idsupitem.in_(
                    DBSession.query(
                        SupItem.idsupitem
                    ).outerjoin(
                        (HighLevelService.__table__,
                            HighLevelService.__table__.c.idservice ==
                            SupItem.__table__.c.idsupitem)
                    ).filter(
                        SupItem.__table__.c.itemtype ==
                        HighLevelService.__mapper_args__['polymorphic_identity']
                    ).filter(HighLevelService.__table__.c.idservice == None)
                )
            ).delete(synchronize_session=False)
        LOGGER.debug("Deleted %d ghosts [SupItem]", nb_ghosts)


        # 3a- MapLinks censés être des MapServiceLink mais qui n'ont
        #     pas d'entrée dans la table MapServiceLink.
        nb_ghosts = DBSession.query(
                MapLink.__table__
            ).filter(
                MapLink.__table__.c.idmaplink.in_(
                    DBSession.query(
                        MapLink.idmaplink
                    ).outerjoin(
                        (MapServiceLink.__table__,
                            MapServiceLink.__table__.c.idmapservicelink ==
                            MapLink.__table__.c.idmaplink)
                    ).filter(
                        MapLink.__table__.c.type_link.in_([
                            MapLlsLink.__mapper_args__['polymorphic_identity'],
                            MapHlsLink.__mapper_args__['polymorphic_identity'],
                        ])
                    ).filter(MapServiceLink.__table__.c.idmapservicelink ==
                             None)
                )
            ).delete(synchronize_session=False)

        # 3b- MapLinks censés être des MapSegment mais qui n'ont
        #     pas d'entrée dans la table MapSegment.
        nb_ghosts += DBSession.query(
                MapLink.__table__
            ).filter(
                MapLink.__table__.c.idmaplink.in_(
                    DBSession.query(
                        MapLink.idmaplink
                    ).outerjoin(
                        (MapSegment.__table__,
                            MapSegment.__table__.c.idmapsegment ==
                            MapLink.__table__.c.idmaplink)
                    ).filter(
                        MapLink.__table__.c.type_link ==
                            MapSegment.__mapper_args__['polymorphic_identity']
                    ).filter(MapSegment.__table__.c.idmapsegment == None)
                )
            ).delete(synchronize_session=False)
        LOGGER.debug("Deleted %d ghosts [MapLink]", nb_ghosts)


        # 4a- MapNodes qui sont censés être des MapNodeHost mais qui
        #     n'ont pas d'entrée dans la sous-table.
        nb_ghosts = DBSession.query(
                MapNode.__table__
            ).filter(
                MapNode.__table__.c.idmapnode.in_(
                    DBSession.query(
                        MapNode.idmapnode
                    ).outerjoin(
                        (MapNodeHost.__table__,
                            MapNodeHost.__table__.c.idmapnode ==
                            MapNode.__table__.c.idmapnode)
                    ).filter(
                        MapNode.__table__.c.type_node ==
                            MapNodeHost.__mapper_args__['polymorphic_identity']
                    ).filter(MapNodeHost.__table__.c.idmapnode == None)
                )
            ).delete(synchronize_session=False)

        # 4b- MapNodes qui sont censés être des MapNodeService mais qui
        #     n'ont pas d'entrée dans la sous-table.
        nb_ghosts += DBSession.query(
                MapNode.__table__
            ).filter(
                MapNode.__table__.c.idmapnode.in_(
                    DBSession.query(
                        MapNode.idmapnode
                    ).outerjoin(
                        (MapNodeService.__table__,
                            MapNodeService.__table__.c.idmapnode ==
                            MapNode.__table__.c.idmapnode)
                    ).filter(
                        MapNode.__table__.c.type_node.in_([
                            MapNodeLls.__mapper_args__['polymorphic_identity'],
                            MapNodeHls.__mapper_args__['polymorphic_identity'],
                        ])
                    ).filter(MapNodeService.__table__.c.idmapnode == None)
                )
            ).delete(synchronize_session=False)
        LOGGER.debug("Deleted %d ghosts [MapNode]", nb_ghosts)


        # Suppression des hôtes qui ont été supprimés dans les fichiers
        # modifiés.
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
        LOGGER.debug("Cleaning up old graphs")
        empty_graphs = DBSession.query(
                Graph
            ).filter(
                Graph.idgraph.in_(
                    DBSession.query(
                            Graph.idgraph
                        ).outerjoin(
                            (GRAPH_PERFDATASOURCE_TABLE,
                                GRAPH_PERFDATASOURCE_TABLE.c.idgraph ==
                                Graph.idgraph
                            ),
                        ).filter(GRAPH_PERFDATASOURCE_TABLE.c.idgraph == None
                    )
                )
            ).delete(synchronize_session=False)
        LOGGER.debug("Removed %r obsolete graphs", empty_graphs)

        # Si on a changé quelque chose, on le note en BDD.
        if hostnames or removed or deleted_hosts or empty_graphs:
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
        hostgroups_cache = set()
        for g in DBSession.query(SUPITEM_GROUP_TABLE.c.idgroup).filter(
            SUPITEM_GROUP_TABLE.c.idsupitem == host.idhost).all():
            hostgroups_cache.add(g.idgroup)

        # Suppression des anciens groupes
        # qui ne sont plus associés à l'hôte.
        for idgroup in hostgroups_cache.copy():
            path = self.group_cache[idgroup]
            if path not in hostdata['otherGroups']:
                DBSession.query(SupItemGroup2SupItem
                    ).filter(SupItemGroup2SupItem.idgroup == idgroup
                    ).filter(SupItemGroup2SupItem.idsupitem == host.idhost
                    ).delete()
                hostgroups_cache.discard(idgroup)

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
            hostgroups_cache.add(idgroup)

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
            ).all()

    def load_conf(self):
        services = conf.hostsConf[self.host.name]['services'].keys()
        collector = None

        # Si le service Collector fait partie des services de l'hôte,
        # alors il doit être traité en premier, pour permettre aux services
        # passifs qui en dépendent d'y faire référence.
        try:
            services.remove('Collector')
        except ValueError:
            pass
        else:
            services.insert(0, 'Collector')

        for service in services:
            reroute = None

            # Si le service dépend du Collector, on récupère
            # l'ID du Collector pour faire le lien entre les deux.
            if (service, 'service') in \
                conf.hostsConf[self.host.name]['SNMPJobs']:
                reroute = collector

            # L'hôte est rerouté, on récupère l'ID du service de reroutage.
            elif conf.hostsConf[self.host.name]['services'] \
                [service]['reRoutedBy']:
                reRoutedBy = conf.hostsConf[self.host.name]['services'] \
                    [service]['reRoutedBy']
                reroute = LowLevelService.get_supitem(
                    reRoutedBy['host'], reRoutedBy['service'])

            service = unicode(service)

            lls = dict(host=self.host, servicename=service)
            if isinstance(reroute, int):
                lls['idcollector'] = reroute
            elif reroute != None:
                lls['collector'] = reroute
            lls = self.add(lls)

            # on mémorise l'identifiant du Collector pour les
            # services passifs à venir qui en dépendent.
            if service == 'Collector':
                collector = lls

            # tags
            if service in conf.hostsConf[self.host.name]['services']:
                tag_loader = TagLoader(lls, conf.hostsConf[self.host.name] \
                    ['services'][service].get('tags', {}))
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

    def __init__(self, host, graphgroups):
        super(GraphLoader, self).__init__(Graph, "name")
        self.host = host
        self.graphgroups = graphgroups

        # Mise en cache des données de performance de l'hôte.
        pds = {}
        for datasource in DBSession.query(PerfDataSource).filter(
            PerfDataSource.idhost == self.host.idhost).all():
            pds[datasource.name] = datasource
        self.pds = pds

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

    def add(self, data):
        """
        Ajoute ou met à jour les liens vers les PerfDataSources et les
        GraphGroups, en plus de la création/mise à jour du graphe lui-même.

        @param data: Dictionnaire contenant les attributs du graphe
            et leurs nouvelles valeurs.
        @type data: C{dict}
        @return: Instance du graphe créé ou mis à jour.
        @rtype: C{Graph}
        """
        graph = super(GraphLoader, self).add(data)
        graphname = data["name"]
        graphdata = conf.hostsConf[self.host.name]['graphItems'][graphname]

        # lien avec les PerfDataSources
        graph.perfdatasources = [self.pds[dsname]
                                 for dsname in graphdata['ds']]

        # lien avec les GraphGroups
        groups = []
        for groupname, graphnames in \
            conf.hostsConf[self.host.name]['graphGroups'].iteritems():
            if graphname in graphnames:
                groups.append(self.graphgroups[groupname])
        graph.groups = groups

        return graph
