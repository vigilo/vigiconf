#!/usr/bin/env python
# -*- coding: utf-8 -*-
################################################################################
#
# ConfigMgr configuration files generation wrapper
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
Générateur de cartes automatiques basique.

"""

class BasicAutoMap(AutoMap):
    """ Implémentation d'un générateur de cartes automatiques.
    
    Les spécifications sont les suivantes:
    
    * la génération est paramétrable au moyen d'un fichier en conf, automaps.py dans le répertoire conf.d/general.
    * Un jeu de groupe de cartes est généré de façon paramétrable, dont un groupe de cartes par groupe de plus haut niveau.
    * Une carte (entité Map) est générée pour un groupe terminal (dans la hiérarchie des groupes) contenant des éléments à superviser (hôtes ou services), si cette carte n'existe pas.
    * lorsqu'une carte est créée, elle est associée à un ou plusieurs groupes de cartes, dont la hiérarchie suit celle des groupes d'éléments à superviser correspondants.
    * Le contenu d'une carte (éléments de classe MapNodeHost et MapNodeHls) est généré si la carte est une carte générée automatiquement.
    * Dans le cas d'une carte générée automatiquement, les éléments affichant des entités n'existant plus sont supprimés. 
    * Les modifications d'un élément affiché dans une carte générée automatiquement ne sont pas prises en compte.
    
    La génération est paramétrable au moyen du fichier en conf
    general/automaps.py; ce fichier contient des données de fond de carte
    comme ceci:
    
        'map_defaults': {
           'background_color': u'white',
           'background_image': u'bg',
           'background_position': u'top right',
           'background_repeat': u'no-repeat',
           'host_icon':u'server',
           'hls_icon':u'switch',
           'lls_icon':u'serviceicon'
        }
        
    Le paramétrage de la génération est effectué comme dans l'exemple suivant:
    
        'BasicAutoMap': {
            'parent_topgroup':None,
        }



    @ivar parent_topgroup: nom du groupe à positionner comme parent pour\
          les groupes de premier niveau à générer.
    """
    
    # voir conf.d/general/automaps.py : param_maps_auto['BasicAutoMap']['parent_topgroup']
    parent_topgroup = None
    
    def __init__(self):
        """Constructeur. """
        AutoMap.__init__(self)
        conf = self.get_conf()
        self.parent_topgroup = conf.param_maps_auto['BasicAutoMap']['parent_topgroup']
        if not self.parent_topgroup:
            # XXX: dossier "virtuel" de plus haut niveau. Hardcodé pour l'instant
            self.parent_topgroup = "Root"
    
    def process_top_group(self, group):
        """ génération des entités liées à un groupe d'hosts de niveau supérieur.
        
        @param group: groupe de premier niveau
        @type group: C{SupItemGroup}
        """
        # génération des MapGroup
        if group.has_children():
            gmap = self.get_or_create_mapgroup(group.name,
                                       parent_name=self.parent_topgroup)
        # génération de la Map
        self.generate_map(group, mapgroups=[self.parent_topgroup,])
    
    def process_leaf_group(self, group):
        """ traitement des hostgroups de niveau final
        
        @param group: groupe de niveau final
        @type group: C{SupItemGroup}
        """
        from vigilo.models.tables import Map
        # génération des Map
        self.generate_map(group)
        # on fait la hiérarchie des mapgroup
        map = Map.by_map_title(group.name)
        if not map:
            return
        if group.has_parent():
            gmap = self.build_mapgroup_hierarchy(group.get_parent())
            #print "map %s groups[0]=%s" % (group.name, gmap.name)
            map.groups = [gmap,]
            DBSession.flush()
    
    def generate_map(self, group, mapgroups=[]):
        """ génère une carte à partir d'un groupe d'éléments supervisés.
        
        @param group: groupe associé à la carte
        @type group: C{SupItemGroup}
        @param mapgroups: liste de noms de groupes de cartes à associer à\
               la carte
        @type mapgroups: C{List}
        """
        nbelts = len(group.get_hosts()) + len(group.get_services())
        if nbelts == 0:
            return
        map = Map.by_map_title(group.name)
        created = False
        if not map:
            map = self.create_map(group.name, mapgroups, self.map_defaults)
            created = True
            #print "map %s genererated groups[0]=%s" % (group.name, map.groups[0].name)
        if map.generated:
            # on gère le contenu uniquement pour les cartes auto
            self.populate_map(map, group, self.map_defaults, created=created)
        DBSession.flush()
        
    def populate_map(self, map, group, data, created=True):
        """ ajout de contenu dans une carte.
        
        @param map: carte
        @type map: C{Map}
        @param group: groupe associé à la carte
        @type group: C{SupItemGroup}
        @param data: dictionnaire de données fond de carte
        @type data: C{Dic}
        """
        from sqlalchemy import and_
        # ajout des nodes hosts
        hosts = list(group.get_hosts())
        for host in hosts:
            # on regarde si un node existe
            nodes = DBSession.query(MapNodeHost).filter(
                                            and_(MapNodeHost.map == map,
                                                 MapNodeHost.host == host)
                                            ).all()
            if not nodes:
                node = MapNodeHost(label=host.name,
                                   map=map,
                                   host=host,
                                   widget=u"ServiceElement",
                                   icon=unicode(data['host_icon']))
                DBSession.add(node)
            else:
                if len(nodes) > 1:
                    raise Exception("host has more than one node in a map")
                # on ne fait rien sur ls éléments présents
        
        # ajout des nodes services
        services = list(group.get_services())
                
        for service in services:
            # on regarde si un node existe
            nodes = DBSession.query( MapNodeHls ).filter(
                                        and_(MapNodeHls.map == map,
                                             MapNodeHls.service == service)
                                            ).all()
            
            if not nodes:
                node = MapNodeHls(label=service.servicename,
                                    map=map,
                                    service=service,
                                    widget=u"ServiceElement",
                                    icon=unicode(data['hls_icon']))
                DBSession.add(node)
            else:
                if len(nodes) > 1:
                    raise Exception("service Hls has more than one node in a map")
                # on ne fait rien sur les éléments présents
        
        # on supprime les éléments qui ne font pas partie des éléments
        # qu'on devrait ajouter (on fait ça seulement pour les cartes auto)
        if map.generated:
            nodes = DBSession.query(MapNodeHost)\
                        .filter(MapNodeHost.map == map)
            # nodes dont les hosts ne font plus partie du groupe group
            for node in nodes:
                if not node.host in hosts:
                    DBSession.delete(node)
            
            nodes = DBSession.query(MapNodeHls)\
                        .filter(MapNodeHls.map == map)
            # nodes dont les services ne font plus partie du groupe group
            for node in nodes:
                if not node.service in services:
                    DBSession.delete(node)
