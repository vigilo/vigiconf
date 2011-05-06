#!/usr/bin/env python
# -*- coding: utf-8 -*-
################################################################################
#
# ConfigMgr configuration files generation wrapper
# Copyright (C) 2007-2011 CS-SI
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

from vigilo.models.tables import MapGroup, Map
from vigilo.models.session import DBSession

from vigilo.vigiconf.lib.exceptions import VigiConfError
from .base import Generator, SkipGenerator

from vigilo.common.gettext import translate
_ = translate(__name__)


__all__ = ("MapGenerator",)


class MapGenerator(Generator):
    """ Classe de base pour un générateur de cartes auto.

    Un générateur de cartes automatiques doit dériver cette classe
    et redéfinir:

    * process_top_group
    * process_mid_group
    * process_leaf_group

    @cvar map_defaults: les réglages par défaut pour les cartes à créer. Les
        instructions "background_*" sont du CSS, voir la doc du W3C:
        U{http://w3schools.com/css/css_reference.asp}
    @type map_defaults: C{dict}
    """

    map_defaults = {'background_color': '',
                    'background_image': '',
                    'background_position': '',
                    'background_repeat': '',
                    'host_icon': 'server',
                    'hls_icon': 'network-workgroup',
                    'lls_icon': 'applications-system',
                    }

    # dossier "virtuel" de plus haut niveau
    # Hardcodé pour l'instant
    rootgroup_name = "Root"

    def __init__(self, application, ventilation):
        super(MapGenerator, self).__init__(application, ventilation)
        self.map_defaults.update(self.application.getConfig())

    def generate_host(self, hostname, vserver):
        raise NotImplementedError()

    def get_root_group(self):
        root = MapGroup.by_parent_and_name(None, unicode(self.rootgroup_name))
        if root:
            return root
        raise SkipGenerator(_("The map group %s has not been added "
                        "by the install procedure") % self.rootgroup_name)

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
            gmap = MapGroup(name=group.name)
            if group.has_parent():
                pgmap = self.build_mapgroup_hierarchy(group.parent)
                gmap.parent = pgmap
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
            gmap = MapGroup(name=name, parent=parent)
            DBSession.add(gmap)
        return gmap

    def create_map(self, title, groups, data=None):
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
        if data is None:
            data = {}
        full_data = self.map_defaults.copy()
        full_data.update(data)
        new_map = Map(title=unicode(title), generated=True,
                mtime=datetime.now(),
                background_color=unicode(full_data['background_color']),
                background_image=unicode(full_data['background_image']),
                background_position=unicode(full_data['background_position']),
                background_repeat=unicode(full_data['background_repeat']),
                )
        new_map.groups = groups
        DBSession.add(new_map)
        return new_map
