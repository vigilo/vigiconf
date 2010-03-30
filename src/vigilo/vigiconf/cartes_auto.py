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
from vigilo.models import HostGroup, MapGroup
from vigilo.models.configure import DBSession

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
            self.gen_map_topgroup(group, self.params['top_groups']['map_group'])
    
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
        for name in context['groups']:
            gname = name % {'hostgroup':group.name}
            if not MapGroup.by_group_name(gname):
                gmap = MapGroup(name=gname)
                parent = context['parent']
                if parent:
                    gmap.parent = MapGroup.by_group_name(parent)
                DBSession.add(gmap)
        DBSession.flush()
                
            
    
    def gen_map_midgroup(self, group, context):
        pass
    
    def gen_map_leafgroup(self, group, context):
        pass
