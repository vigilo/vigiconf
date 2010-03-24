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

from vigilo.models import HostGroup, ServiceGroup

from vigilo.models.configure import DBSession

class GroupLoader(XMLLoader):
    """ Classe de base pour charger des fichiers XML groupes .
    
    Peut être directement instanciée, ou comme c'est le cas
    pour les groupes d'hosts ou de services, être utilisée comme
    classe de base.
    """
    
    # should be set in subclass
    _classgroup = None
    _tag_group = None
    
    def __init__(self, classgroup=None, tag_group=None, xsd_filename=None):
        """
        @param classgroup Modèle (ex. HostGroup ou ServiceGroup)
        @type  classgroup: C{class}
        @param tag_group balise xml "hostgroup" or "servicegroup"
        @type  tag_group: C{str}
        @param xsd_filename fichier schema xsd pour validation
        @type  xsd_filename: C{str}
        """
        if classgroup: self._classgroup = classgroup
        if tag_group: self._tag_group = tag_group
        if xsd_filename: self._xsd_filename = xsd_filename
        XMLLoader.__init__(self)

    
    def load(self, path):
        """ Charge des groupes génériques depuis un fichier xml.
        
            @param filepath: an XML file
            @type  filepath: C{str}
        """
        parent_stack = []
        current_parent = None
        deleting_mode = False
        
        classgroup = self._classgroup
        tag_group = self._tag_group
        
        try:
            for event, elem in self.get_xml_parser(path):
                if event == "start":
                    if elem.tag == tag_group:
                        name = unicode(elem.attrib["name"].strip())
                        group = classgroup.by_group_name(groupname=name)
                        if not group:
                            group = classgroup(name=name)
                            DBSession.add(group)
                        else:
                            if deleting_mode:
                                DBSession.delete(group)
                                continue
                            
                            group.children = []
                        
                        if current_parent:
                            if group.parent:
                                if group.parent.name != current_parent.name:
                                    raise Exception(
                    "%s %s should have one parent (%s, %s)" %
                    (tag_group, group.name, group.parent.name,
                     current_parent.name)
                                        )
                            group.parent = current_parent
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
        except:
            raise


# VIGILO_EXIG_VIGILO_CONFIGURATION_0010 : Fonctions de préparation des
#   configurations de la supervision en mode CLI
#
#   configuration des groupes d'hôtes : ajout/modification/suppression d'un
#   groupe d'hôte
class HostGroupLoader(GroupLoader):
    _classgroup = HostGroup
    _tag_group = "hostgroup"
    _xsd_filename = "hostgroup.xsd"
    
    def delete_all(self):
        """ efface la totalité des entités de la base
        
        """
        DBSession.query(HostGroup).delete()
    
    def get_hosts_conf(self):
        """ reconstruit le dico hostsGroup v1
        
        TODO: refactoring
        """
        hostsgroups = {}
        for g in DBSession.query(HostGroup).all():
            hostsgroups[g.name] = g.name
        return hostsgroups
    
    def get_groups_hierarchy(self):
        """ reconstruit le dico groupsHierarchy v1
        
        TODO: refactoring
        """
        hgroups = {}
        for top in HostGroup.get_top_groups():
            hgroups[top.name] = self._get_children_hierarchy(top)
        return hgroups
    
    def _get_children_hierarchy(self, hostgroup):
        """ fonction récursive construisant un dictionnaire hiérarchique.
        """
        if hostgroup.children == []:
            return 1
        hchildren = {}
        for g in hostgroup.children:
            hchildren[g.name] = self._get_children_hierarchy(g)
        return hchildren
        


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
    _classgroup = ServiceGroup
    _tag_group = "servicegroup"
    _xsd_filename = "servicegroup.xsd"
    
    def delete_all(self):
        """ efface la totalité des entités de la base
        
        """
        DBSession.query(ServiceGroup).delete()

