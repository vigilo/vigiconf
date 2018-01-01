# -*- coding: utf-8 -*-
# vim:set expandtab tabstop=4 shiftwidth=4:
# Copyright (C) 2007-2018 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Generic exceptions for the Vigilo Config Manager
"""


class VigiConfError(Exception):
    """Exception VigiConf générique"""

    def __init__(self, value):
        super(VigiConfError, self).__init__(value)
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

class DispatchatorError(VigiConfError):
    """The exception type raised by instances of Dispatchator"""
    pass



# vim:set expandtab tabstop=4 shiftwidth=4:
