# -*- coding: utf-8 -*-
"""
Générateur de cartes automatiques pour les groupes
"""

from __future__ import absolute_import

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

from vigilo.models import tables
from vigilo.models.session import DBSession

from vigilo.vigiconf.lib.generators import MapGenerator


class VigiMapGen(MapGenerator):
    """
    Implémentation d'un générateur automatique de cartes pour les groupes.
    Les spécifications sont les suivantes :

    * la génération est paramétrable au moyen d'un fichier en conf, automaps.py
    dans le répertoire conf.d/general.
    * Un jeu de groupes de cartes est généré de façon paramétrable, dont un
    groupe de cartes par groupe de plus haut niveau.
    * Une carte (entité Map) est générée pour un groupe terminal (dans la
    hiérarchie des groupes) contenant des éléments à superviser (hôtes ou
    services), si cette carte n'existe pas.
    * lorsqu'une carte est créée, elle est associée à un ou plusieurs groupes
    de cartes, dont la hiérarchie suit celle des groupes d'éléments à
    superviser correspondants.
    * Le contenu d'une carte (éléments de classe MapNodeHost et MapNodeHls) est
    généré si la carte est une carte générée automatiquement.
    * Dans le cas d'une carte générée automatiquement, les éléments affichant
    des entités n'existant plus sont supprimés.
    * Les modifications d'un élément affiché dans une carte générée
    automatiquement ne sont pas prises en compte.
    """
    # pylint: disable-msg=R0201

    def __init__(self, application, ventilation):
        super(VigiMapGen, self).__init__(application, ventilation)
        self.current_hierarchy = {}
        self.new_hierarchy = {}

    def get_root_group(self):
        group_name = self.map_defaults['parent_topgroup']
        if not group_name:
            return super(VigiMapGen, self).get_root_group()
        top_group = super(VigiMapGen, self).get_root_group()
        return self.get_or_create_mapgroup(group_name, top_group)

    def populate_map(self, map, group, data=None):
        """ ajout de contenu dans une carte.

        @param map: carte
        @type map: C{vigilo.models.tables.Map}
        @param group: groupe associé à la carte
        @type group: C{vigilo.models.tables.SupItemGroup}
        @param data: dictionnaire de données fond de carte
        @type data: C{dict}
        """
        if data is None:
            data = {}
        full_data = self.map_defaults.copy()
        full_data.update(data)
        self._populate_hosts(map, group, full_data)
        self._populate_lls(map, group, full_data)
        self._populate_hls(map, group, full_data)

    def _populate_hosts(self, map, group, data):
        """ajout des nodes Host"""
        nodes = DBSession.query(tables.MapNodeHost).filter(
                        tables.MapNodeHost.map == map).all()
        for host in group.hosts:
            host_nodes = [n for n in nodes if n.idhost == host.idhost]
            # on regarde si un node existe
            if len(host_nodes) > 1:
                # Plus d'une icône pour un même hôte ? On efface tout et on
                # recommence.
                for node in host_nodes:
                    DBSession.delete(node)
                DBSession.flush()
                host_nodes = []
            if not host_nodes:
                node = tables.MapNodeHost(label=host.name,
                                          map=map,
                                          host=host,
                                          widget=u"ServiceElement",
                                          icon=unicode(data['host_icon']))
                DBSession.add(node)
                # on ne fait rien sur ls éléments présents
        # on supprime les éléments qui ne font pas partie du groupe
        for node in nodes:
            allowed_ids = [ h.idhost for h in group.hosts ]
            if node.idhost not in allowed_ids:
                DBSession.delete(node)
        #DBSession.flush()

    def _populate_lls(self, map, group, data):
        """ajout des nodes LowLevelService"""
        nodes = DBSession.query(tables.MapNodeLls).filter(
                    tables.MapNodeLls.map == map).all()
        for service in group.lls:
            svc_nodes = [n for n in nodes if n.idservice == service.idservice]
            # on regarde si un node existe
            if len(svc_nodes) > 1:
                # Plus d'une icône pour un même service ? On efface tout et on
                # recommence.
                for node in svc_nodes:
                    DBSession.delete(node)
                DBSession.flush()
                svc_nodes = []
            if not svc_nodes:
                node = tables.MapNodeLls(label=service.servicename,
                                         map=map,
                                         service=service,
                                         widget=u"ServiceElement",
                                         icon=unicode(data['lls_icon']))
                DBSession.add(node)
        # on supprime les éléments qui ne font pas partie du groupe
        for node in nodes:
            allowed_ids = [ s.idservice for s in group.lls ]
            if node.service not in allowed_ids:
                DBSession.delete(node)
        #DBSession.flush()

    def _populate_hls(self, map, group, data):
        """ajout des nodes HighLevelService"""
        nodes = DBSession.query(tables.MapNodeHls).filter(
                        tables.MapNodeHls.map == map).all()
        for service in group.hls:
            svc_nodes = [n for n in nodes if n.idservice == service.idservice]
            # on regarde si un node existe
            if len(svc_nodes) > 1:
                # Plus d'une icône pour un même hls ? On efface tout et on
                # recommence.
                for node in svc_nodes:
                    DBSession.delete(node)
                DBSession.flush()
                nodes = []
            if not svc_nodes:
                node = tables.MapNodeHls(label=service.servicename,
                                         map=map,
                                         service=service,
                                         widget=u"ServiceElement",
                                         icon=unicode(data['hls_icon']))
                DBSession.add(node)
        # on supprime les éléments qui ne font pas partie du groupe
        for node in nodes:
            allowed_ids = [ s.idservice for s in group.hls ]
            if node.service not in allowed_ids:
                DBSession.delete(node)
        #DBSession.flush()

    def _make_mapgroup(self, supitemgroup, parent_mapgroup):
        existing = tables.MapGroup.by_parent_and_name(parent_mapgroup,
                                                      supitemgroup.name)
        if existing:
            LOGGER.debug("Using existing MapGroup for group %s",
                         supitemgroup.name)
            return existing
        LOGGER.debug("Creating MapGroup for group %s", supitemgroup.name)
        return tables.MapGroup(name=supitemgroup.name, parent=parent_mapgroup)

    def _make_map(self, supitemgroup, parent_mapgroup):
        existing = tables.Map.by_group_and_title(parent_mapgroup,
                                                 supitemgroup.name)
        if existing:
            LOGGER.debug("Using existing Map for group %s", supitemgroup.name)
            return existing
        LOGGER.debug("Creating Map for SupItemGroup %(group)s in MapGroup "
                     "%(mapgroup)s", {"group": supitemgroup.name,
                                      "mapgroup": parent_mapgroup.name})
        newmap = self.create_map(supitemgroup.name, [parent_mapgroup, ])
        return newmap

    def _remove_mapgroup(self, mapgroup):
        """
        Équivalent d'un gros "rm -rf" bien bourrin. Supprime aussi les
        sous-cartes.
        """
        LOGGER.debug("Removing MapGroup %s and its children", mapgroup.name)
        abort_deletion = False
        for submapgroup in mapgroup.get_all_children():
            has_manual_maps = False
            for m in submapgroup.maps:
                if not m.generated:
                    has_manual_maps = True
                    continue # On ne supprime que les cartes autogénérées
                DBSession.delete(m)
            if has_manual_maps:
                abort_deletion = True
            else:
                DBSession.delete(submapgroup)
        if not abort_deletion:
            DBSession.delete(mapgroup)

    def _group_has_subgroups(self, group):
        """
        Plus subtil qu'un simple has_children(), parce qu'il faut ignorer les
        groupes qui ne contiennent rien
        """
        if not group.has_children():
            return False
        for subgroup in group.get_all_children():
            if subgroup.supitems:
                return True
        return False

    def _walk_hierarchy(self, parent_supitemgroup=None, parent_mapgroup=None):
        """
        Parcourre le contenu d'un SupItemGroup, mis en parallèle à un MapGroup.
        Pour chaque fils, elle appelle L{_handle_supitemgroup} qui fait la
        création de ce qu'il faut. Ensuite, on supprime ce qui était là avant
        et dont on ne veut plus.

        Cette fonction est appelée récursivement (par L{_handle_supitemgroup},
        pas par elle-même).

        @param parent_supitemgroup: Le groupe à parcourir
        @type  parent_supitemgroup: C{vigilo.models.tables.SupItemGroup}
        @param parent_mapgroup: Le groupe de cartes où créer les cartes associées
        @type  parent_mapgroup: C{vigilo.models.tables.MapGroup}
        @returns: Liste des objets créés
        @rtype: C{list} de C{vigilo.models.tables.Map}s
            ou de C{vigilo.models.tables.MapGroup}s
        """
        if parent_supitemgroup is None:
            supitemgroups = tables.SupItemGroup.get_top_groups()
        else:
            supitemgroups = parent_supitemgroup.children
        if parent_mapgroup is None:
            parent_mapgroup = self.get_root_group()
        results = []
        for supitemgroup in supitemgroups:
            result = self._handle_supitemgroup(supitemgroup, parent_mapgroup)
            results.extend(result)
        allowed_subgroups = [ r.name for r in results if isinstance(r, tables.MapGroup) ]
        allowed_submaps  = [ r.title for r in results if isinstance(r, tables.Map) ]
        for submapgroup in parent_mapgroup.children:
            if submapgroup.name not in allowed_subgroups:
                self._remove_mapgroup(submapgroup)
        for submap in parent_mapgroup.maps:
            if submap.title not in allowed_submaps and submap.generated:
                LOGGER.debug("Removing Map for group %s", submap.title)
                DBSession.delete(submap)

    def _handle_supitemgroup(self, supitemgroup, parent_mapgroup):
        """
        Traite un groupe, c'est à dire créée les Map et les MapGroups en
        fonction du contenu
        """
        results = []
        if self._group_has_subgroups(supitemgroup):
            mapgroup = self._make_mapgroup(supitemgroup, parent_mapgroup)
            results.append(mapgroup)
            self._walk_hierarchy(supitemgroup, mapgroup)
        if supitemgroup.supitems:
            newmap = self._make_map(supitemgroup, parent_mapgroup)
            results.append(newmap)
            self.populate_map(newmap, supitemgroup)
        return results

    def generate(self):
        LOGGER.debug("Generating maps for the host groups")
        self._walk_hierarchy()
        DBSession.flush()
