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

from .xmlloader import XMLLoader, ET

from datetime import datetime

from vigilo.models import Map

from vigilo.models.configure import DBSession

class MapLoader(XMLLoader):
    
    do_validation = True

    def load(self, path):
        """ Loads maps from a xml file.
        
            @param filepath: an XML file
            @type  filepath: C{str}
        """
        
        maps = {}
        
        try:
            for event, elem in ET.iterparse(path, events=("start", "end")):
                if event == "start":
                    if elem.tag == "map":
                        mapid = elem.attrib["id"].strip()
                        groups = []
                    elif elem.tag == "title":
                        title = unicode(elem.text.strip())
                    elif elem.tag == "bg_position":
                        bg_position = unicode(elem.text.strip())
                    elif elem.tag == "bg_repeat":
                        bg_repeat = unicode(elem.text.strip())
                    elif elem.tag == "bg_color":
                        bg_color = unicode(elem.text.strip())
                    elif elem.tag == "bg_image":
                        bg_image = unicode(elem.text.strip())
                    elif elem.tag == "group":
                        groups.append(unicode(elem.text.strip()))
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
                        if mapid:
                            maps[mapid] = map
                        mapid = None
                            
                        
            DBSession.flush()
        except:
            #DBSession.rollback()
            raise
