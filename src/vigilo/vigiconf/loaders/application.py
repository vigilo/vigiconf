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

from vigilo.models.tables import Application

from vigilo.vigiconf.lib.loaders import DBLoader


__docformat__ = "epytext"


class ApplicationLoader(DBLoader):
    """
    Charge les applications en base depuis le modèle mémoire.
    """

    def __init__(self, apps):
        self.apps = apps
        super(ApplicationLoader, self).__init__(Application, "name")

    def load_conf(self):
        for app_obj in self.apps:
            app = dict(name=unicode(app_obj.name))
            self.add(app)

