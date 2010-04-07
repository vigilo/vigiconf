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

from vigilo.models.tables import HostGroup, MapGroup, Map
from vigilo.models.session import DBSession

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
        for top in HostGroup.get_top_groups():
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
            self.gen_map_midgroup(group, self.params['mid_groups']['map_group'])
    
    def process_leaf_group(self, group):
        """ traitement des hostgroups de niveau final
        """
        if self.params['leaf_groups']['map_group']['generate']:
            self.gen_map_leafgroup(group, self.params['leaf_groups']['map_group'])
    
    def _process_children(self, group):
        """ méthode récursive pour traiter les hiérarchies de groupes
        """
        for g in group.children:
            if len(g.children) > 0:
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
            if not MapGroup.by_group_name(gname):
                gmap = MapGroup(name=gname)
                parent = context['map_group']['parent']
                if parent:
                    gmap.parent = MapGroup.by_group_name(parent)
                DBSession.add(gmap)
                
                # génération des Map
                if context['map']['generate']:
                    map = Map.by_map_title(gmap.name)
                    if not map:
                        self.create_map(gname, (gmap,), context['map']['defaults'])
        DBSession.flush()
    
    def gen_map_midgroup(self, group, context):
        pass
    
    def gen_map_leafgroup(self, group, context):
        pass
    
    def create_map(self, title, groups, data):
        map = Map(title=title, generated=True,
                  mtime=datetime.now(),
                  background_color=data['background_color'],
                  background_image=data['background_image'],
                  background_position=data['background_position'],
                  background_repeat=data['background_repeat']
                  )
        map.groups = list(groups)
        DBSession.add(map)
