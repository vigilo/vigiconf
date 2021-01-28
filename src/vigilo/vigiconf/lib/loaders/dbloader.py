# -*- coding: utf-8 -*-
# Copyright (C) 2007-2021 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>
"""
Ce module permet de mettre à jour la base de données vigilo en supprimant
les objets qui ne sont plus en conf.
"""

__docformat__ = "epytext"

from sqlalchemy.ext import associationproxy
from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

from vigilo.models.session import DBSession
from vigilo.vigiconf.lib import ParsingError


class DBLoader(object):
    """
    Classe abstraite de chargement des données de la configuration, avec
    gestion de la synchronisation avec la base de données.

    La méthode load doit être redéfinie obligatoirement.
    """

    def __init__(self, cls, key_attr=None):
        self._class = cls
        self._key_attr = key_attr
        self.__in_db = None # géré sous forme de propriété, voir plus bas
        self._in_conf = {}

    def load(self):
        self.load_conf()
        self.cleanup()
        DBSession.flush()

    def load_conf(self):
        """
        Charge les données depuis la configuration.
        Cette méthode doit être redéfinie dans une classe dérivée.
        Elle fait appel à self.add quand une instance est chargée.
        """
        raise NotImplementedError(_("The 'load' method must be redefined"))

    def add(self, data):
        """
        @param data: un dictionnaire des données à insérer ou à mettre à jour
        @type  data: C{dict}
        """
        if self.is_in_db(data):
            instance = self.update(data)
        else:
            instance = self.insert(data)
        #DBSession.flush()
        return instance

    def cleanup(self):
        for inst_key in self._in_db:
            if inst_key not in self._in_conf.keys():
                self.delete(self._in_db[inst_key])

    def is_in_db(self, data):
        """
        @param data: un dictionnaire des données à insérer ou à mettre à jour
        @type  data: C{dict}
        """
        if self.get_key(data) in self._in_db.keys():
            return True
        else:
            return False

    @property
    def _in_db(self):
        """Charge toutes les instances depuis la base de données"""
        if self.__in_db is not None:
            return self.__in_db
        self.__in_db = {}
        for inst in self._list_db():
            self.__in_db[self.get_key(inst)] = inst
        return self.__in_db

    def _list_db(self):
        return DBSession.query(self._class).all()

    def get_key(self, data):
        """
        Retourne une clé identifiante de l'instance.

        Cette méthode sera probablement redéfinie pour les loaders de classes
        plus complexes (notamment si la clé primaire est partagée sur deux
        colonnes).

        @param data: un dictionnaire des données à insérer ou à mettre à jour
        @type  data: C{dict}
        """
        if self._key_attr is None:
            raise NotImplementedError(_("The key attribute must be defined, "
                                "or the get_key() method must be redefined"))
        if isinstance(data, self._class):
            return getattr(data, self._key_attr)
        else:
            return data[self._key_attr]

    # Access to a protected member ... of a client class
    # Désactivé car on doit accéder à des classes semi-publiques de SQLAlchemy.
    # pylint: disable-msg=W0212
    def update(self, data):
        """
        @param data: un dictionnaire des données à mettre à jour
        @type  data: C{dict}
        """
        # @TODO: il faudrait mutualiser ce code avec insert dans add.
        key = self.get_key(data)
        if key in self._in_conf:
            raise ParsingError(_(
                'Trying to override configuration for '
                'already-defined entity "%(entity)s"') % {
                    'entity': key,
                })

        LOGGER.debug("Updating: %(key)s (%(class)s)", {
            'key': key,
            'class': self._class.__name__,
        })
        instance = self._in_db[key]

        # Ces types surviennent fréquemment et sont compatibles
        # (en terme d'interface) même s'ils ne sont pas liés entre
        # eux en terme d'héritage (cf. #904).
        compatible_types = {
            dict: associationproxy._AssociationDict,
            list: associationproxy._AssociationList,
            set: associationproxy._AssociationSet,
            associationproxy._AssociationDict: dict,
            associationproxy._AssociationList: list,
            associationproxy._AssociationSet: set,
        }

        for attr, value in data.iteritems():
            old_value = getattr(instance, attr)
            old_type = type(old_value)
            new_type = type(value)
            if old_type != new_type and \
                compatible_types.get(old_type) != new_type:
                LOGGER.debug("WARNING: Different types between old and new "
                             "value, comparison will always fail. "
                             "Old is %(old_value)s (%(old_type)r), "
                             "new is %(new_value)s (%(new_type)r).", {
                                    'old_value': old_value,
                                    'old_type': old_type,
                                    'new_value': value,
                                    'new_type': new_type,
                             })
            if old_value != value:
                LOGGER.debug("Updating property %(property)s from "
                             "%(old_value)s (%(old_type)r) to "
                             "%(new_value)s (%(new_type)r)", {
                                    'property': attr,
                                    'old_value': old_value,
                                    'old_type': old_type,
                                    'new_value': value,
                                    'new_type': new_type,
                             })
                setattr(instance, attr, value)
        self._in_conf[key] = instance
        return instance

    def insert(self, data):
        # @TODO: il faudrait mutualiser ce code avec update dans add.
        key = self.get_key(data)
        if key in self._in_conf:
            raise ParsingError(_(
                'Trying to override configuration for '
                'already-defined entity "%(entity)s"') % {
                    'entity': key,
                })
        LOGGER.debug("Inserting: %s", key)
        instance = self._class(**data) # pylint: disable-msg=W0142
        DBSession.add(instance)
        self._in_conf[key] = instance
        return instance

    def delete(self, instance): # pylint: disable-msg=R0201
        LOGGER.debug("Deleting: %s", instance)
        DBSession.delete(instance)
