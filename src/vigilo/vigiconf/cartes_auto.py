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
from datetime import datetime

from vigilo.models.tables import SupItemGroup, MapGroup, Map
from vigilo.models.tables import MapNodeHost, MapNodeService
from vigilo.models.session import DBSession

from sqlalchemy import and_

"""
Manager de cartes automatiques.

Un manager de carte automatique est une classe héritant de la classe
CartesAutoManager.
"""

class CartesAutoManager:
    """ Classe de base pour un manager de cartes auto
    """
    def init(self, params):
        """ charge les paramètres de génération
        
        TODO: fichier xml
        """
        self.params = params
    
    def process(self):
        """ lance la génération des cartes auto
        """
        for top in SupItemGroup.get_top_groups():
            self.process_top_group(top)
            self._process_children(top)
            
    def process_top_group(self, group):
        """ traitement des hostgroups de haut niveau
        """
        if self.params['top_groups']['map_group']['generate']:
            self.gen_map_topgroup(group, self.params['top_groups'])
    
    def process_mid_group(self, group):
        """ traitement des hostgroups de niveau intermédiaire
        """
        if self.params['mid_groups']['map_group']['generate']:
            self.gen_map_midgroup(group, self.params['mid_groups'])
    
    def process_leaf_group(self, group):
        """ traitement des hostgroups de niveau final
        """
        if self.params['leaf_groups']['map_group']['generate']:
            self.gen_map_leafgroup(group, self.params['leaf_groups'])
    
    def _process_children(self, group):
        """ méthode récursive pour traiter les hiérarchies de groupes
        """
        for g in group.get_children():
            if g.has_children():
                self.process_mid_group(g)
                self._process_children(g)          
            else:
                self.process_leaf_group(g)
    
    def gen_map_topgroup(self, group, context):
        """ génération des entités liées à un groupe d'hosts de niveau supérieur.
        
        création d'un MapGroup de même nom que le groupe
        création des MapGroups de niveau supérieur
        création d'une Map portant le même nom que le groupe
        """
        # génération des MapGroup
        for name in context['map_group']['groups']:
            gname = name % {'hostgroup':group.name}
            
            if not context['map_group'].has_key('parent'):
                context['map_group']['parent'] = None
                
            if not MapGroup.by_group_name(gname):
                gmap = MapGroup(name=gname)
                parent = context['map_group']['parent']
                if parent:
                    gmap.set_parent(MapGroup.by_group_name(parent))
                DBSession.add(gmap)
                
                # génération des Map
                if context['map']['generate']:
                    map = Map.by_map_title(gmap.name)
                    created = False
                    if not map:
                        map = self.create_map(gname, (gmap,), context['map']['defaults'])
                        created = True
                    if map.generated:
                        # on gère le contenu uniquement pour les cartes auto
                        self.populate_map(map, group, context['map']['defaults'], created=created)
                        
        DBSession.flush()
    
    def gen_map_midgroup(self, group, context):
        pass
    
    def gen_map_leafgroup(self, group, context):
        # on fait comme pour les top groups
        self.gen_map_topgroup(group, context)
    
    def create_map(self, title, groups, data):
        """ création d'une carte
        """
        map = Map(title=title, generated=True,
                  mtime=datetime.now(),
                  background_color=data['background_color'],
                  background_image=data['background_image'],
                  background_position=data['background_position'],
                  background_repeat=data['background_repeat']
                  )
        map.groups = list(groups)
        DBSession.add(map)
        return map
    
    def populate_map(self, map, group, data, created=True):
        """ ajout de contenu dans une carte
        """
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
                                   hosticon=data['hosticon'],
                                   hoststateicon=data['hoststateicon'])
                DBSession.add(node)
            else:
                if len(nodes) > 1:
                    raise Exception("host has more than one node in a map")
                # on ne fait rien sur ls éléments présents
        
        # ajout des nodes services
        services = list(group.get_services())
        for service in services:
            # on regarde si un node existe
            nodes = DBSession.query(MapNodeService).filter(
                                        and_(MapNodeService.map == map,
                                             MapNodeService.service == service)
                                            ).all()
            
            if not nodes:
                node = MapNodeService(label=service.servicename,
                                    map=map,
                                    service=service,
                                    serviceicon=data['serviceicon'],
                                    servicestateicon=data['servicestateicon'])
                DBSession.add(node)
            else:
                if len(nodes) > 1:
                    raise Exception("service has more than one node in a map")
                # on ne fait rien sur ls éléments présents
        
        # on supprime les éléments qui ne font pas partie des éléments
        # qu'on devrait ajouter (on fait ça seulement pour les cartes auto)
        if map.generated:
            nodes = DBSession.query(MapNodeHost)\
                        .filter(MapNodeHost.map == map)
            # nodes dont les hosts ne font plus partie du groupe group
            for node in nodes:
                if not node.host in hosts:
                    DBSession.delete(node)
            
            nodes = DBSession.query(MapNodeService)\
                        .filter(MapNodeService.map == map)
            # nodes dont les services ne font plus partie du groupe group
            for node in nodes:
                if not node.service in services:
                    DBSession.delete(node)
                
                
