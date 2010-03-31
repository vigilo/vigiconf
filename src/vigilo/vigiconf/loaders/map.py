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
    
    def start_element(self, tag):
        """ 
        """
        pass
    
    def end_element(self, tag):
        """
        """
        pass
    
    
    def load(self, path):
        """ Loads maps from a xml file.
        
            @param filepath: an XML file
            @type  filepath: C{str}
        """
        
        maps = {}
        node_mode = False
        submap_mode = False
        
        try:
            for event, elem in self.get_xml_parser(path):
                if event == "start":
                    if elem.tag == "map":
                        mapid = self.get_uattrib("id", elem)
                        groups = []
                    elif elem.tag == "nodes":
                        node_mode = True
                    elif elem.tag == "host":
                        if not node_mode: continue
                        name = elem.attrib["name"].strip()
                        id = elem.attrib["id"].strip()
                        host = Host.by_host_name(name)
                    elif elem.tag == "service":
                        if not node_mode: continue
                        pass
                    elif elem.tag == "label":
                        pass
                    elif elem.tag == "position":
                        pass
                    elif elem.tag == "icon":
                        pass
                    elif elem.tag == "stateicon":
                        pass
                    elif elem.tag == "submaps":
                        submap_mode = True
                    elif elem.tag == "title":
                        title = self.get_utext(elem)
                    elif elem.tag == "bg_position":
                        bg_position = self.get_utext(elem)
                    elif elem.tag == "bg_repeat":
                        bg_repeat = self.get_utext(elem)
                    elif elem.tag == "bg_color":
                        bg_color = self.get_utext(elem)
                    elif elem.tag == "bg_image":
                        bg_image = self.get_utext(elem)
                    elif elem.tag == "group":
                        groupname = self.get_utext(elem)
                        group = MapGroup.by_group_name(groupname)
                        if not group:
                            group = MapGroup(name=groupname)
                        groups.append(group)
                        
                else:
                    if elem.tag == "map":
                        map = Map(
                                mtime=datetime.today(),
                                title=title,
                                background_color=bg_color,
                                background_image=bg_image,
                                background_position=bg_position,
                                background_repeat=bg_repeat
                                )
                        if len(groups) > 0:
                            map.groups = list(groups)
                        if mapid:
                            maps[mapid] = map
                        mapid = None
                    elif elem.tag == "nodes":
                        node_mode = False
                    elif elem.tag == "host":
                        if not node_mode: continue
                        pass
                    elif elem.tag == "service":
                        if not node_mode: continue
                        pass
                    elif elem.tag == "host":
                        if not node_mode: continue
                        host, name, id = (None,) * 3
                    elif elem.tag == "submaps":
                        submap_mode = False
                            
                        
            DBSession.flush()
        except:
            #DBSession.rollback()
            raise
