# -*- coding: utf-8 -*-
################################################################################
#
# VigiConf
# Copyright (C) 2007-2016 CS-SI
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
Basic generator for the Vigilo Config Manager
"""

import os

from vigilo.common.conf import settings
from vigilo.common.gettext import translate
_ = translate(__name__)

from vigilo.vigiconf.lib.exceptions import VigiConfError


class SkipGenerator(VigiConfError):
    pass


class Generator(object):
    """
    La classe de base pour les générateurs

    @ivar ventilation: correspondance entre les hôtes, les applications et les
        serveurs Vigilo
    @type ventilation: C{dict}, voir la méthode
        L{vigilo.vigiconf.lib.ventilation.Ventilator.ventilate}()
    @cvar deploy_only_on_first: Drapeau indiquant si l'on doit déployer
        uniquement sur le premier serveur Vigilo disponible (C{True})
        ou bien sur l'ensemble des serveurs disponibles (C{False}).
    """
    deploy_only_on_first = True

    def __init__(self, application, ventilation):
        self.application = application
        self.ventilation = ventilation
        self.baseDir = os.path.join(settings["vigiconf"].get("libdir"),
                                    "deploy")
        self.results = {"errors": [], "warnings": []}

    def __str__(self):
        return "<Generator for %s>" % (self.application.name)

    def generate(self):
        """
        La méthode principale de génération. Peut-être réimplémentée par des
        sous-classes si besoin.
        """
        for hostname in self.ventilation.keys():
            if self.application.name not in self.ventilation[hostname]:
                continue
            vservers = self.ventilation[hostname][self.application.name]
            if isinstance(vservers, basestring):
                vservers = [vservers, ]
            for vserver in vservers:
                self.generate_host(hostname, vserver)

                # On ne doit déployer que sur
                # le premier élément de la liste.
                if self.deploy_only_on_first:
                    break

    def generate_host(self, hostname, vserver):
        """
        La génération de conf pour un hôte et son serveur associé.
        @note: À implémenter dans les sous-classes
        """
        raise NotImplementedError(_("Generators must define the "
                                    "generate_host() method"))

    def addWarning(self, element, msg):
        """
        Add a warning
        @param element: the element emitting the warning (usually a host)
        @type  element: C{str}
        @param msg: the warning message
        @type  msg: C{str}
        """
        self.results["warnings"].append( (element, msg) )

    def addError(self, element, msg):
        """
        Add a error
        @param element: the element emitting the error (usually a host)
        @type  element: C{str}
        @param msg: the error message
        @type  msg: C{str}
        """
        self.results["errors"].append( (element, msg) )

    def get_vigilo_servers(self):
        vservers = set()
        for ventilation in self.ventilation.values():
            if self.application.name not in ventilation:
                continue
            vservers.add(ventilation[self.application.name])
        return vservers

    def write_scripts(self):
        self.application.write_startup_scripts(self.baseDir)
        self.application.write_validation_script(self.baseDir)
