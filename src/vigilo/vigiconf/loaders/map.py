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

from datetime import datetime

from vigilo.models.tables import Map, MapGroup, Host, LowLevelService

from vigilo.models.session import DBSession

from .xmlloader import XMLLoader

class MapLoader(XMLLoader):
    
    do_validation = True
    
    maps = {}
    node_mode = False
    submap_mode = False
    groups = None
    
    def start_element(self, tag):
        """ start element event handler
        """
        if   tag == "map": self.start_map()
        elif tag == "nodes": self.node_mode = True
        elif tag == "host": self.start_host()
        elif tag == "service": pass
        elif tag == "label": self.start_label()
        elif tag == "position": pass
        elif tag == "icon": pass
        elif tag == "stateicon": pass
        elif tag == "submaps": self.submap_mode = True
        elif tag == "title": self.title = self.get_utext()
        elif tag == "bg_position": self.bg_position = self.get_utext()
        elif tag == "bg_repeat": self.bg_repeat = self.get_utext()
        elif tag == "bg_color": self.bg_color = self.get_utext()
        elif tag == "bg_image": self.bg_image = self.get_utext()
        elif tag == "group": self.start_group()
        elif tag == "maps": pass
        elif tag == "links": pass
        elif tag == "servicelink": pass
        elif tag == "segment": pass
        elif tag == "reference": pass
        elif tag == "from_node": pass
        elif tag == "to_node": pass
        else:
            raise Exception("balise inconnue: <%s>" % tag)
    
    def end_element(self, tag):
        """ end element event handler
        """
        if   tag == "map": self.end_map()
        elif tag == "nodes": self.node_mode = False
        elif tag == "host": self.end_host()
        elif tag == "service": pass
        elif tag == "label": self.end_label()
        elif tag == "position": pass
        elif tag == "icon": pass
        elif tag == "stateicon": pass
        elif tag == "submaps": self.submap_mode = False
        elif tag == "title": pass
        elif tag == "bg_position": pass
        elif tag == "bg_repeat": pass
        elif tag == "bg_color": pass
        elif tag == "bg_image": pass
        elif tag == "group": self.end_group()
        elif tag == "maps": pass
        elif tag == "links": pass
        elif tag == "servicelink": pass
        elif tag == "segment": pass
        elif tag == "reference": pass
        elif tag == "from_node": pass
        elif tag == "to_node": pass
        else:
            raise Exception("balise inconnue: <%s>" % tag)
        
    def start_map(self):
        self.mapid = self.get_uattrib("id")
        self.groups = []
    
    def end_map(self):
        map = Map(
                mtime=datetime.today(),
                title=self.title,
                background_color=self.bg_color,
                background_image=self.bg_image,
                background_position=self.bg_position,
                background_repeat=self.bg_repeat
                )
        if len(self.groups) > 0:
            map.groups = list(self.groups)
        if self.mapid:
            self.maps[self.mapid] = map
        self.mapid = None
        
    
    def start_host(self):
        if not self.node_mode: return
        
        name = self.get_attrib("name")
        id = self.get_attrib("id")
        host = Host.by_host_name(name)
    
    def end_host(self):
        if not self.node_mode: return
        host, name, id = (None,) * 3
     
    def start_group(self):
        groupname = self.get_utext()
        group = MapGroup.by_group_name(groupname)
        if not group:
            group = MapGroup(name=groupname)
        self.groups.append(group)
    
    def end_group(self):
        pass
    
    def start_label(self):
        pass
    
    def end_label(self):
        pass
    
    def start_(self):
        pass
    
    def end_(self):
        pass
   
