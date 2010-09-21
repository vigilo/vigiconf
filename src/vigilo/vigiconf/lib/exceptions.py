# -*- coding: utf-8 -*-
################################################################################
#
# Copyright (C) 2007-2010 CS-SI
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
Generic exceptions for the Vigilo Config Manager
"""


class VigiConfError(Exception):
    """Generic VigiConf Exception"""

    def __init__(self, value):
        super(VigiConfError, self).__init__()
        self.value = value

    def __repr__(self):
        return repr(self.value)

    def __str__(self):
        return self.value


class EditionError(VigiConfError):
    """
    Exception raised when Entreprise Edition features are called in the
    Community Edition
    """
    pass

class ParsingError(VigiConfError):
    """
    Exception raised when parsing of the configuration files failed
    """
    pass

# vim:set expandtab tabstop=4 shiftwidth=4:
