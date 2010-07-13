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

import os

from vigilo.common.conf import settings
from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

from vigilo.models.tables import SupItemGroup
from vigilo.models.tables.grouphierarchy import GroupHierarchy

from vigilo.models.session import DBSession

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib.xmlloader import XMLLoader

class GroupLoader(XMLLoader):
    """ Classe de base pour charger des fichiers XML groupes .
    
    Peut être directement instanciée, ou comme c'est le cas
    pour les groupes d'hosts ou de services, être utilisée comme
    classe de base.
        
    @ivar _tag_group: balise xml "hostgroup" or "servicegroup"
    @type _tag_group: C{str}
    @ivar _xsd_filename: fichier schema xsd pour validation
    @type _xsd_filename: C{str}
    """
    
    _tag_group = "group"
    _xsd_filename = "group.xsd"
    
    def __init__(self):
        super(GroupLoader, self).__init__(SupItemGroup, "name")

    def load_conf(self):
        confdir = settings['vigiconf'].get('confdir')
        self.load_dir(os.path.join(confdir, 'groups'))
        # les groupes se chargent maintenant avec loader XML
        conf.hostsGroups = self.get_hosts_conf()
        conf.groupsHierarchy = self.get_groups_hierarchy()

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
        for g in group.children:
            hchildren[unicode(g.name)] = self._get_children_hierarchy(g)
        return hchildren

    def update(self, data):
        instance = super(GroupLoader, self).update(data)
        instance.set_parent(self._current_parent)
        DBSession.flush()
        return instance

    def insert(self, data):
        LOGGER.debug(_("Inserting: %s"), self.get_key(data))
        instance = self._class.create(data["name"], self._current_parent)
        self._in_conf[self.get_key(data)] = instance
        DBSession.flush()
        return instance

    def delete(self, instance):
        instance.remove_children()
        super(GroupLoader, self).delete(instance)

    def start_element(self, elem):
        if elem.tag == self._tag_group:
            name = unicode(elem.attrib["name"].strip())
            # update parent stack
            if len(self._parent_stack):
                self._current_parent = self._parent_stack[-1]
            else:
                self._current_parent = None
            instance = self.add({"name": name})
            self._parent_stack.append(instance)

    def end_element(self, elem):
        if elem.tag == self._tag_group:
            if len(self._parent_stack):
                self._parent_stack.pop()

            if len(self._parent_stack):
                self._current_parent = self._parent_stack[-1]
            else:
                self._current_parent = None

    def load_file(self, path):
        """ Charge des groupes génériques depuis un fichier xml.
        
        @param path: an XML file
        @type  path: C{str}
        """
        
        self._parent_stack = []
        self._current_parent = None
        return super(GroupLoader, self).load_file(path)


## VIGILO_EXIG_VIGILO_CONFIGURATION_0010 : Fonctions de préparation des
##   configurations de la supervision en mode CLI
##
##   configuration des groupes d'hôtes : ajout/modification/suppression d'un
##   groupe d'hôte
#class HostGroupLoader(GroupLoader):
#    
#    _tag_group = "hostgroup"
#    _xsd_filename = "hostgroup.xsd"
#
#    def get_hosts_conf(self):
#        """ reconstruit le dico hostsGroup v1
#        
#        TODO: refactoring
#        """
#        hostsgroups = {}
#        for g in DBSession.query(SupItemGroup).all():
#            hostsgroups[g.name] = g.name
#        return hostsgroups
#
#
## VIGILO_EXIG_VIGILO_CONFIGURATION_0010 : Fonctions de préparation des
##   configurations de la supervision en mode CLI
##
##   configuration d'un groupe de service : ajout/modification/suppression d'un
##     groupe de service
##   configuration des services de haut niveau : ajout/modification/suppression
##     d'un service
##   configuration des règles de corrélations associé à un service de haut
##     niveau : ajout/modification/suppression d'une règle de corrélation
#class ServiceGroupLoader(GroupLoader):
#
#    _tag_group = "servicegroup"
#    _xsd_filename = "servicegroup.xsd"

