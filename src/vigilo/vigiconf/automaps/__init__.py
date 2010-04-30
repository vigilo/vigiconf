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
import glob
import sys
import os
import os.path
import types

from datetime import datetime

from vigilo.models.tables import SupItemGroup, MapGroup, Map
from vigilo.models.session import DBSession

class AutoMap:
    """ Classe de base pour un manager de cartes auto.
    
    Un générateur de cartes automatiques doit dériver cette classe
    et redéfinir:
    
    * process_top_group
    * process_mid_group
    * process_leaf_group
    
    """
    
    map_defaults = {'background_color': u'white',
                   'background_image': u'bg',
                   'background_position': u'top right',
                   'background_repeat': u'no-repeat',
                   'host_icon':u'hosticon',
                   'hls_icon':u'serviceicon',
                   'lls_icon':u'serviceicon'
                   }
    
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
    
    
    def get_groupmap(self, group):
        """ recursive
        """
        gmap = MapGroup.by_group_name(group.name)
        if not gmap:
            gmap = MapGroup(name=group.name)
            if group.has_parent():
                pgmap = self.get_groupmap(group.get_parent())
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

class AutoMapManager(object):
    """
    Handles the generator library.
    @cvar genclasses: the list of available generators.
    @type genclasses: C{list}
    
    TODO: factoriser avec generators
    """

    genclasses = []

    def __init__(self):
        if not self.genclasses:
            self.__load()

    def __load(self):
        """Load the available generators"""
        generator_files = glob.glob(os.path.join(
                                os.path.dirname(__file__), "*.py"))
        for filename in generator_files:
            if os.path.basename(filename).startswith("__"):
                continue
            try:
                execfile(filename, globals(), locals())
            except Exception, e:
                sys.stderr.write("Error while parsing %s: %s\n" \
                                 % (filename, str(e)))
                raise
        for name, genclass in locals().iteritems():
            if isinstance(genclass, (type, types.ClassType)):
                if issubclass(genclass, AutoMap) and  name != "AutoMap":
                    self.genclasses.append(genclass)
            elif isinstance(genclass, (type, types.ModuleType)) and \
                    name not in globals():
                # This is an import statement and we don't have it yet,
                # re-bind it here
                globals()[name] = genclass
                continue

    def generate(self):
        """Execute each subclass' generate() method"""
        for genclass in self.genclasses:
            generator = genclass()
            generator.generate()
