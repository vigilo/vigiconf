# -*- coding: utf-8 -*-
################################################################################
#
# VigiConf
# Copyright (C) 2007-2011 CS-SI
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
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
Générateur pour le client local VigiConf

Pour l'instant, il ne créé que les scripts de démarrage et d'arrêt qui ont été
spécifiés dans L{conf.apps}, sur tous les serveurs Vigilo déclarés.

@todo: ne générer les scripts d'une application que si elle est effectivement
    installée sur le serveur Vigilo considéré (mineur).
"""

from __future__ import absolute_import

import os

from vigilo.models.session import DBSession
from vigilo.models import tables

from .. import conf
from . import FileGenerator

class VigiConfLocal(FileGenerator):

    def generate(self):
        vservers = DBSession.query(tables.VigiloServer.name).all()
        if vservers is None:
            return
        for vserver in [v.name for v in vservers]:
            for appname, appdata in conf.apps.iteritems():
                basedir = os.path.join(self.baseDir, vserver,
                                       "vigiconf-local", appname)
                if not os.path.exists(basedir):
                    os.makedirs(basedir)
                if not appdata["startMethod"]:
                    appdata["startMethod"] = "return true"
                if not appdata["stopMethod"]:
                    appdata["stopMethod"] = "return true"
                for action in ["start", "stop"]:
                    script = open(os.path.join(basedir, "%s.sh" % action), "w")
                    script.write("#!/bin/sh\n%s\n" % appdata["%sMethod" % action])
                    script.close()


# vim:set expandtab tabstop=4 shiftwidth=4:
