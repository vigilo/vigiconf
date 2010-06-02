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

from .xmlloader import XMLLoader

from vigilo.models.tables import SupItemGroup
from vigilo.models.tables.grouphierarchy import GroupHierarchy

from vigilo.models.session import DBSession

from ..lib.dbupdater import DBUpdater

class GroupLoader(XMLLoader):
    """ Classe de base pour charger des fichiers XML groupes .
    
    Peut être directement instanciée, ou comme c'est le cas
    pour les groupes d'hosts ou de services, être utilisée comme
    classe de base.
    """
    
    _classgroup = SupItemGroup
    _tag_group = "group"
    _xsd_filename = "group.xsd"
    
    def __init__(self, tag_group=None, xsd_filename=None):
        """ Constructeur.
        
        @param tag_group: balise xml "hostgroup" or "servicegroup"
        @type  tag_group: C{str}
        @param xsd_filename: fichier schema xsd pour validation
        @type  xsd_filename: C{str}
        """
        self._classgroup = SupItemGroup
        if tag_group: self._tag_group = tag_group
        if xsd_filename: self._xsd_filename = xsd_filename
        XMLLoader.__init__(self)
        # gestion de la suppression des groupes non lus
        self.dbupdater = DBUpdater(self._classgroup, "name")

    
    def delete_all(self):
        """ efface la totalité des entités de la base
        
        """
        DBSession.query(GroupHierarchy).delete()
        DBSession.query(SupItemGroup).delete()
    
    def get_hosts_conf(self):
        """ reconstruit le dico hostsGroup v1
        
        TODO: refactoring
        """
        hostsgroups = {}
        for g in DBSession.query(SupItemGroup).all():
            uname = unicode(g.name)
            hostsgroups[uname] = uname
        return hostsgroups
    
    def get_groups_hierarchy(self):
        """ reconstruit le dico groupsHierarchy v1
        
        TODO: refactoring
        """
        hgroups = {}
        for top in SupItemGroup.get_top_groups():
            uname = unicode(top.name)
            hgroups[uname] = self._get_children_hierarchy(top)
        return hgroups
    
    def _get_children_hierarchy(self, group):
        """ fonction récursive construisant un dictionnaire hiérarchique.
        
        @param group: an XML file
        @type  group: C{Group}
        """
        if not group.has_children():
            return 1
        hchildren = {}
        for g in group.get_children():
            hchildren[unicode(g.name)] = self._get_children_hierarchy(g)
        return hchildren

    
    def load(self, path):
        """ Charge des groupes génériques depuis un fichier xml.
        
        @param path: an XML file
        @type  path: C{str}
        """
        
        parent_stack = []
        current_parent = None
        deleting_mode = False
        
        classgroup = self._classgroup
        tag_group = self._tag_group
        
        for event, elem in self.get_xml_parser(path):
            if event == "start":
                if elem.tag == tag_group:
                    name = unicode(elem.attrib["name"].strip())
                    
                    self.dbupdater.in_conf(name)
                    
                    group = classgroup.by_group_name(groupname=name)
                    if not group:
                        group = classgroup.create(name=name)
                        DBSession.add(group)
                    else:
                        if deleting_mode:
                            DBSession.delete(group)
                            continue
                        
                        group.remove_children()
                    
                    if current_parent:
                        if group.has_parent():
                            if group.get_parent().name != current_parent.name:
                                raise Exception(
                "%s %s should have one parent (%s, %s)" %
                (tag_group, group.name, group.get_parent().name,
                 current_parent.name)
                                    )
                        group.set_parent(current_parent)
                    # update parent stack
                    parent_stack.append(group)
                elif elem.tag == "children":
                    current_parent = parent_stack[-1]
                elif elem.tag == "todelete":
                    deleting_mode = True
            else:
                if elem.tag == tag_group:
                    if len(parent_stack) > 0:
                        parent_stack.pop()
                elif elem.tag == "children":
                    current_parent = None
                elif elem.tag == "todelete":
                    deleting_mode = False
        DBSession.flush()


# VIGILO_EXIG_VIGILO_CONFIGURATION_0010 : Fonctions de préparation des
#   configurations de la supervision en mode CLI
#
#   configuration des groupes d'hôtes : ajout/modification/suppression d'un
#   groupe d'hôte
class HostGroupLoader(GroupLoader):
    _classgroup = SupItemGroup
    _tag_group = "hostgroup"
    _xsd_filename = "hostgroup.xsd"
    
    
    def get_hosts_conf(self):
        """ reconstruit le dico hostsGroup v1
        
        TODO: refactoring
        """
        hostsgroups = {}
        for g in DBSession.query(SupItemGroup).all():
            hostsgroups[g.name] = g.name
        return hostsgroups
       


# VIGILO_EXIG_VIGILO_CONFIGURATION_0010 : Fonctions de préparation des
#   configurations de la supervision en mode CLI
#
#   configuration d'un groupe de service : ajout/modification/suppression d'un
#     groupe de service
#   configuration des services de haut niveau : ajout/modification/suppression
#     d'un service
#   configuration des règles de corrélations associé à un service de haut
#     niveau : ajout/modification/suppression d'une règle de corrélation
class ServiceGroupLoader(GroupLoader):
    _classgroup = SupItemGroup
    _tag_group = "servicegroup"
    _xsd_filename = "servicegroup.xsd"

