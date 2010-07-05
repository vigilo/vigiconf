#!/usr/bin/env python
# -*- coding: utf-8 -*-
################################################################################
#
# ConfigMgr Nagios Collector plugin configuration file generator
# Copyright (C) 2007 CS-SI
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
Generators for the Vigilo Config Manager

"""

class Generator(object):
    """
    La classe de base pour les générateurs

    @ivar mapping: mapping de ventilation
    @type mapping: C{dict}, voir L{lib.ventilator.findAServerForEachHost}()
    @ivar validator: validator instance for warnings and errors
    @type validator: L{Validator<lib.validator.Validator>}
    """

    def __init__(self, mapping, validator):
        self.mapping = mapping
        self.validator = validator
        validator.addAGenerator()

    def __str__(self):
        return self.__class__.__name__.replace("Tpl","")

    def generate(self):
        """
        The main generation method.
        @note: To be reimplemented by sub-classes
        """
        raise NotImplementedError("Genrators must define the generate() method")

    def addWarning(self, element, msg):
        """
        Add a warning in the validator
        @param element: the element emitting the warning (usually a host)
        @type  element: C{str}
        @param msg: the warning message
        @type  msg: C{str}
        """
        self.validator.addWarning(str(self), element, msg)

    def addError(self, element, msg):
        """
        Add a error in the validator
        @param element: the element emitting the error (usually a host)
        @type  element: C{str}
        @param msg: the error message
        @type  msg: C{str}
        """
        self.validator.addError(str(self), element, msg)


