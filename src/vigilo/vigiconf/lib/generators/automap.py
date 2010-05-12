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
Générateurs de cartes automatiques pour Vigilo
"""

from datetime import datetime

from vigilo.models.tables import SupItemGroup, MapGroup, Map
from vigilo.models.session import DBSession
from ... import conf

class AutoMap:
    """ Classe de base pour un générateur de cartes auto.
    
    Un générateur de cartes automatiques doit dériver cette classe
    et redéfinir:
    
    * process_top_group
    * process_mid_group
    * process_leaf_group
    
    """
    
    # voir conf.d/general/automaps.py : param_maps_auto['AutoMap']['map_defaults']
    map_defaults = {'background_color': u'white',
                   'background_image': u'bg',
                   'background_position': u'top right',
                   'background_repeat': u'no-repeat',
                   'host_icon':u'server',
                   'hls_icon':u'switch',
                   'lls_icon':u'serviceicon'
                   }
    
    def __init__(self):
        conf = self.get_conf()
        self.map_defaults = conf.param_maps_auto['AutoMap']['map_defaults']
    
    def generate(self):
        """ lance la génération des cartes auto
        """
        for top in SupItemGroup.get_top_groups():
            self.process_top_group(top)
            self.process_children(top)
            
    def process_top_group(self, group):
        """ traitement des hostgroups de haut niveau
        """
        pass
    
    def process_mid_group(self, group, parent):
        """ traitement des hostgroups de niveau intermédiaire
        """
        pass
    
    def process_leaf_group(self, group):
        """ traitement des hostgroups de niveau final
        """
        pass
    
    def process_children(self, group):
        """ méthode récursive pour traiter les hiérarchies de groupes
        """
        for g in group.get_children():
            if g.has_children():
                self.process_mid_group(g, parent=group)
                self.process_children(g)          
            else:
                self.process_leaf_group(g)
    
    
    def build_mapgroup_hierarchy(self, group):
        """ recursive
        reconstruit une hiérachie de MapGroup en fonction de la hiérarchie
        du groupe.
        """
        gmap = MapGroup.by_group_name(group.name)
        if not gmap:
            gmap = MapGroup(name=group.name)
            if group.has_parent():
                pgmap = self.build_mapgroup_hierarchy(group.get_parent())
                gmap.set_parent(pgmap)
            DBSession.add(gmap)
        return gmap
        
    def get_or_create_mapgroup(self, name, parent_name=None):
        gmap = MapGroup.by_group_name(name)
        if not gmap:
            gmap = MapGroup(name=name)
            if parent_name:
                gmap.set_parent(self.get_or_create_mapgroup(parent_name))
            DBSession.add(gmap)
        return gmap
    
    def create_map(self, title, groupnames, data):
        """ création d'une carte
        """
        map = Map(title=title, generated=True,
                  mtime=datetime.now(),
                  background_color=data['background_color'],
                  background_image=data['background_image'],
                  background_position=data['background_position'],
                  background_repeat=data['background_repeat']
                  )
        map.groups = []
        for name in groupnames:
            map.groups.append(MapGroup.by_group_name(name))
        DBSession.add(map)
        return map
    
    def session(self):
        return DBSession
    
    def get_conf(self):
        return conf
