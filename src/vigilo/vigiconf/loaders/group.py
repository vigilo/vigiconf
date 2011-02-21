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

from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import and_

from vigilo.common.conf import settings
from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

from vigilo.models.tables import SupItemGroup
from vigilo.models.session import DBSession

from vigilo.vigiconf.lib.loaders import XMLLoader


class GroupLoader(XMLLoader):
    """ Classe de base pour charger des fichiers XML groupes .

    Peut être directement instanciée, ou comme c'est le cas
    pour les groupes d'hosts ou de services, être utilisée comme
    classe de base.

    @ivar _tag_group: balise xml qui permet de définir les groupes ("group")
    @type _tag_group: C{str}
    @ivar _xsd_filename: fichier schema xsd pour validation
    @type _xsd_filename: C{str}

    VIGILO_EXIG_VIGILO_CONFIGURATION_0010 : Fonctions de préparation des
    configurations de la supervision en mode CLI :
        - configuration d'un group d'hôtes : ajout/modification/suppression
            d'un hôte
        - configuration d'un groupe de services : ajout/modification/
            suppression d'un service
        - configuration des services de haut niveau : ajout/modification/
            suppression d'un service
        - configuration des règles de corrélations associé à un service de haut
            niveau : ajout/modification/suppression d'une règle de corrélation
    """

    _tag_group = "group"
    _xsd_filename = "group.xsd"
    _root = u'/Root'

    def __init__(self, dispatchator):
        super(GroupLoader, self).__init__(SupItemGroup)
        self.__in_db = {}
        self.dispatchator = dispatchator

        # On récupère tous les groupes déjà en base et on génère un cache
        # (groupnames) de leurs noms formattés pour ajout dans un chemin.
        groupnames = {}
        sig_alias = aliased(SupItemGroup)
        instances = DBSession.query(
                SupItemGroup,
                sig_alias.idgroup.label('idchild'),
            ).join(
                (sig_alias, and_(
                    sig_alias._grouptype == SupItemGroup._grouptype,
                    SupItemGroup.left <= sig_alias.left,
                    SupItemGroup.right >= sig_alias.right,
                ))
            ).order_by(
                SupItemGroup.depth.asc(),
                sig_alias.depth.asc(),
            ).all()

        hierarchy = {}
        for grouphierarchy in instances:
            parent = grouphierarchy[0]
            groupnames.setdefault(
                parent.idgroup,
                parent.name
                    .replace('\\', '\\\\')
                    .replace('/', '\\/')
            )

            hierarchy.setdefault(parent.idgroup, {
                'path': u'',
                'ids_path': [],
                'instance': parent,
            })

            hierarchy.setdefault(grouphierarchy.idchild, {
                'path': u'',
                'ids_path': [],
                'instance': None,
            })

            hierarchy[grouphierarchy.idchild]['ids_path'].append(parent.idgroup)
            hierarchy[grouphierarchy.idchild]['path'] += u'/%s' % (
                groupnames[parent.idgroup],
            )
            if grouphierarchy.idchild == parent.idgroup:
                hierarchy[grouphierarchy.idchild]['instance'] = parent
        self._hierarchy = hierarchy

        # Mise en cache des instances existantes, à la fois
        # avec leur identifiant de groupe et avec leur chemin.
        for idgroup, data in self._hierarchy.iteritems():
            self.__in_db[idgroup] = data['instance']
            self.__in_db[data['path']] = data['instance']

    def is_in_db(self, data):
        """
        @param data: un dictionnaire des données à insérer ou à mettre à jour
        @type  data: C{dict}
        """
        if self.get_key(data) in self.__in_db:
            return True
        else:
            return False

    def get_hierarchy(self):
        return self._in_conf

    def load_conf(self):
        self._in_conf = {}
        confdir = settings['vigiconf'].get('confdir')
        self.load_dir(os.path.join(confdir, 'groups'))

    def cleanup(self):
        delete = set()
        for data in self._hierarchy.itervalues():
            if data['path'] not in self._in_conf.keys():
                delete.add(data['path'])

        # On ne supprime jamais le groupe racine.
        delete.discard(self._root)

        ordered = sorted(list(delete), reverse=True)
        for g in ordered:
            self.delete(self.__in_db[g])

    def add(self, data):
        if not data['parent']:
            data['parent'] = self.__in_db[self._root]

        return super(GroupLoader, self).add(data)

    def update(self, data):
        # On ne fait pas appel à la méthode update() de la classe mère
        # car elle exécuterait trop de requêtes SQL pour le même résultat.
        key = self.get_key(data)
        instance = self.__in_db[key]

        LOGGER.debug("Updating: %(key)s (%(class)s)",
                     {'key': key, 'class': self._class.__name__})

        if instance.idgroup is None:
            DBSession.add(instance)
            DBSession.flush()

        # On évite les requêtes SQL lorsqu'il n'y a rien à changer.
        current_idparent = data['parent'].idgroup
        idparent = self._hierarchy[instance.idgroup]['ids_path'][-2]

        if idparent != current_idparent:
            instance.parent = data['parent']
            DBSession.flush()
        self._in_conf[key] = instance
        return instance

    def insert(self, data):
        key = self.get_key(data)
        # Si l'instance a déjà été créée au cours du déploiement,
        # on réutilise l'instance créée. Ceci évite de créer des
        # groupes différents ayant le même chemin (#336).
        if key in self._in_conf:
            return self._in_conf[key]
        LOGGER.debug("Inserting: %s", key)

        instance = self._class(name=data["name"], parent=data["parent"])
        DBSession.add(instance)
        DBSession.flush()

        if data["parent"]:
            ids_path = self._hierarchy[data["parent"].idgroup]["ids_path"]
        else:
            ids_path = []

        self._hierarchy[instance.idgroup] = {
            'path': key,
            'ids_path': ids_path + [instance.idgroup],
            'instance': instance,
        }
        self._in_conf[key] = instance
        DBSession.flush()
        return instance

    def start_element(self, elem):
        if elem.tag == self._tag_group:
            name = unicode(elem.attrib["name"].strip())
            # update parent stack
            if len(self._parent_stack):
                self._current_parent = self._parent_stack[-1]
            else:
                self._current_parent = None

            instance = self.add({"name": name,
                                 "parent": self._current_parent})
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

        self._current_parent = None
        self._parent_stack = []

        instance = self.__in_db[self._root]
        self._in_conf[self._root] = instance
        return super(GroupLoader, self).load_file(path)

    def get_key(self, data):
        if isinstance(data, SupItemGroup):
            if data.idgroup in self._hierarchy:
                return self._hierarchy[data.idgroup]['path']
            return data.get_path()

        if not data['parent']:
            prefix = ""
        else:
            prefix = data["parent"].get_path()

        return "%s/%s" % (
            prefix,
            data["name"]
                .replace('\\', '\\\\')
                .replace('/', '\\/')
        )
