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
Générateur de cartes automatiques pour Vigilo
"""

from datetime import datetime

from vigilo.models.tables import SupItemGroup, MapGroup, Map
from vigilo.models.tables.grouphierarchy import GroupHierarchy
from vigilo.models.session import DBSession

from . import Generator
from ... import conf

class MapGenerator(Generator):
    """ Classe de base pour un générateur de cartes auto.
    
    Un générateur de cartes automatiques doit dériver cette classe
    et redéfinir:
    
    * process_top_group
    * process_mid_group
    * process_leaf_group
    
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
    """
    
    # voir conf.d/general/automaps.py :
    #   param_maps_auto['AutoMap']['map_defaults']
    map_defaults = {'background_color': u'white',
                   'background_image': u'bg',
                   'background_position': u'top right',
                   'background_repeat': u'no-repeat',
                   'host_icon':u'server',
                   'hls_icon':u'switch',
                   'lls_icon':u'serviceicon'
                   }
    
    # dossier "virtuel" de plus haut niveau
    # Hardcodé pour l'instant
    rootgroup_name = "Root"

    def __init__(self, mapping, validator):
        super(MapGenerator, self).__init__(mapping, validator)
        self.map_defaults = conf.param_maps_auto['AutoMap']['map_defaults']

    def get_root_group(self):
        root = MapGroup.by_parent_and_name(None, unicode(self.rootgroup_name))
        if root:
            return root
        raise KeyError("The map group %s has not been added by the install procedure"
                       % self.rootgroup_name)

    def process_top_group(self, group):
        """ traitement des hostgroups de haut niveau
        
        @param group: groupe de premier niveau
        @type group: C{SupItemGroup}
        
        A redéfinir dans la classe dérivée.
        """
        pass
    
    def process_mid_group(self, group, parent):
        """ traitement des hostgroups de niveau intermédiaire
        
        @param group: groupe de premier niveau
        @type group: C{SupItemGroup}
        @param parent: groupe parent
        @type parent: C{SupItemGroup}
        
        A redéfinir dans la classe dérivée.
        """
        pass
    
    def process_leaf_group(self, group):
        """ traitement des hostgroups de niveau final
        
        @param group: groupe de niveau final
        @type group: C{SupItemGroup}
        
        A redéfinir dans la classe dérivée.
        """
        pass
    
    def process_children(self, group):
        """ méthode récursive pour traiter les hiérarchies de groupes
        
        @param group: groupe
        @type group: C{SupItemGroup}
        """
        for g in group.children:
            if g.has_children():
                self.process_mid_group(g, parent=group)
                self.process_children(g)          
            else:
                self.process_leaf_group(g)
    
    
    def build_mapgroup_hierarchy(self, group):
        """ reconstruit une hiérachie de MapGroup en fonction de la hiérarchie
        du groupe. Cette méthode est récursive.
        
        @param group: groupe
        @type group: C{MapGroup}
        """
        gmap = MapGroup.by_group_name(group.name)
        if not gmap:
            gmap = MapGroup.create(name=group.name)
            if group.has_parent():
                pgmap = self.build_mapgroup_hierarchy(group.get_parent())
                gmap.set_parent(pgmap)
            DBSession.add(gmap)
        return gmap
        
    def get_or_create_mapgroup(self, name, parent=None):
        """ renvoie et éventuellement génère un groupe de cartes.
        
        @param name: nom de groupe de carte
        @type  name: C{str}
        @param parent: groupe parent (opt)
        @type  parent: L{MapGroup}
        
        @return: le groupe de cartes
        @rtype:  C{MapGroup}
        """
        name = unicode(name)
        if not parent and name == self.rootgroup_name:
            return self.get_root_group()
        if not parent:
            parent = self.get_root_group()
        gmap = MapGroup.by_parent_and_name(parent, name)
        if not gmap:
            gmap = MapGroup.create(name, parent)
            DBSession.add(gmap)
        return gmap
    
    def create_map(self, title, groups, data):
        """ création d'une carte.
        
        @param title: titre de la carte
        @type  title: C{str}
        @param groups: liste de noms de groupes à associer à la carte
        @type  groups: C{list} de L{MapGroup}
        @param data: dictionnaire de données fond de carte
        @type  data: C{dict}
        
        @return: une carte
        @rtype: C{Map}
        """
        map = Map(title=unicode(title), generated=True,
                  mtime=datetime.now(),
                  background_color=unicode(data['background_color']),
                  background_image=unicode(data['background_image']),
                  background_position=unicode(data['background_position']),
                  background_repeat=unicode(data['background_repeat']),
                  )
        map.groups = groups
        DBSession.add(map)
        return map
    

