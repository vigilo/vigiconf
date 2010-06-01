#!/usr/bin/env python
# -*- coding: utf-8 -*-
################################################################################
#
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
"""
Ce module permet de mettre à jour la base de données vigilo en supprimant
les objets qui ne sont plus en conf.
"""
from vigilo.models.session import DBSession

class DBUpdater:
    _class = None
    _instances = None
    _key_attr = None
    
    def __init__(self, cls, key_attr):
        """ Constructeur.
        """
        self._class = cls
        self._instances = {}
        self._key_attr = key_attr
    
    def load_instances(self):
        """ charge toutes les instances depuis la base de données
        """
        for inst in DBSession.query(self._class).all():
            self._instances[getattr(inst, self._key_attr)] = inst
    
    def in_conf(self, key):
        """ Marque une instance comme étant en conf
        """
        self._instances[key] = None
    
    def update(self):
        """ Mise à jour de la base de données.
        
        Les instances non marquées comme étant en conf sont supprimées.
        """
        for inst in self._instances.values():
            if inst:
                inst.delete()
        DBSession.flush()
    
    
    