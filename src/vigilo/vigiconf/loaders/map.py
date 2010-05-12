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
    hosts = {}
    node_mode = False
    submap_mode = False
    groups = []
    label = None
    
    def start_element(self, tag):
        """ start element event handler
        """
        if   tag == "map":
            if self._bloclist == ['maps', 'map']: self.start_map()
            elif 'submaps' in self._bloclist: self.start_submap()
            else:
                pass
                # print self._bloclist
        elif tag == "nodes": self.node_mode = True
        elif tag == "host": self.start_host()
        elif tag == "service": pass
        elif tag == "label":
            if 'host' in self._bloclist: self.label = self.get_utext()
        elif tag == "position": self.start_position()
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
        if   tag == "map":
            if self._bloclist == ['maps', 'map']: self.end_map()
            elif 'submaps' in self._bloclist: self.end_submap()
            else:
                pass
                #print self._bloclist
        elif tag == "nodes": self.node_mode = False
        elif tag == "host": self.end_host()
        elif tag == "service": pass
        elif tag == "label": pass
        elif tag == "position": pass
        elif tag == "icon": pass
        elif tag == "stateicon": pass
        elif tag == "submaps": self.submap_mode = False
        elif tag == "title": pass
        elif tag == "bg_position": pass
        elif tag == "bg_repeat": pass
        elif tag == "bg_color": pass
        elif tag == "bg_image": pass
        elif tag == "group": pass
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
        DBSession.add(map)
        #print self.title
        if len(self.groups) > 0:
            map.groups = list(self.groups)
            DBSession.flush()
        
        if self.mapid:
            self.maps[self.mapid] = map
        self.mapid = None
        
    
    def start_host(self):
        if not self.node_mode: raise Exception("host node must be in a nodes block.")
        
        name = self.get_uattrib("name")
        id = self.get_attrib("id")
        host = Host.by_host_name(name)
        if not host:
            raise Exception("host %s does not exist" % name)
        self.hosts[id] = host
    
    def end_host(self):
        if not self.node_mode:  raise Exception("host node must be in a nodes block.")
        self.host, self.name, self.id = (None,) * 3
        self.label = None
        self.x, self.y, self.minimize = (None,) * 3
     
    def start_group(self):
        groupname = self.get_utext()
        group = MapGroup.by_group_name(groupname)
        if not group:
            group = MapGroup(name=groupname)
            DBSession.add(group)
        self.groups.append(group)
    
    def start_submap(self):
        pass
    
    def end_submap(self):
        pass
    
    def start_position(self):
        self.x = int(self.get_attrib("x"))
        self.y = int(self.get_attrib("y"))
        self.minimize = self.get_attrib("minimize") == 'true'
    
    def start_(self):
        pass
    
    def end_(self):
        pass
   
