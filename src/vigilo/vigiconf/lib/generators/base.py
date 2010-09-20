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
Basic generator for the Vigilo Config Manager
"""

import os

from vigilo.common.conf import settings
from vigilo.common.gettext import translate
_ = translate(__name__)

class Generator(object):
    """
    La classe de base pour les générateurs

    @ivar mapping: mapping de ventilation
    @type mapping: C{dict}, voir la méthode
        L{vigilo.vigiconf.lib.ventilator.Ventilator.ventilate}()
    @ivar validator: validator instance for warnings and errors
    @type validator: L{Validator<lib.validator.Validator>}
    """

    def __init__(self, application, mapping, validator):
        self.application = application
        self.mapping = mapping
        self.validator = validator
        validator.addAGenerator()
        self.baseDir = os.path.join(settings["vigiconf"].get("libdir"),
                                    "deploy")

    def __str__(self):
        return "<Generator for %s>" % (self.application.name)

    def generate(self):
        """
        The main generation method.
        @note: To be reimplemented by sub-classes
        """
        raise NotImplementedError(_("Generators must define the generate() method"))

    def addWarning(self, element, msg):
        """
        Add a warning in the validator
        @param element: the element emitting the warning (usually a host)
        @type  element: C{str}
        @param msg: the warning message
        @type  msg: C{str}
        """
        self.validator.addWarning(self.application.name, element, msg)

    def addError(self, element, msg):
        """
        Add a error in the validator
        @param element: the element emitting the error (usually a host)
        @type  element: C{str}
        @param msg: the error message
        @type  msg: C{str}
        """
        self.validator.addError(self.application.name, element, msg)

    def get_vigilo_servers(self):
        vservers = set()
        for hostname, ventilation in self.mapping.iteritems():
            if self.application.name not in ventilation:
                continue
            vservers.add(ventilation[self.application.name])
        return vservers

    def write_scripts(self):
        self.application.write_startup_scripts(self.baseDir)
        self.application.write_validation_script(self.baseDir)

