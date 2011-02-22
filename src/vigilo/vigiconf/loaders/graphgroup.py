# -*- coding: utf-8 -*-
################################################################################
#
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

from vigilo.models.session import DBSession
from vigilo.models.tables import GraphGroup

from vigilo.vigiconf.lib.loaders import DBLoader

from vigilo.vigiconf import conf

__docformat__ = "epytext"


class GraphGroupLoader(DBLoader):
    """
    Charge les groupes de graphes en base depuis le modèle mémoire.
    """

    def __init__(self):
        super(GraphGroupLoader, self).__init__(GraphGroup, "name")

    def load_conf(self):
        groupnames = set()
        for hostname in conf.hostsConf:
            for groupname in conf.hostsConf[hostname]['graphGroups']:
                groupnames.add(unicode(groupname))
        for groupname in groupnames: # déduplication
            self.add({"name": groupname})

    def update(self, data):
        instance = super(GraphGroupLoader, self).update(data)
        DBSession.flush()
        return instance

