#!/usr/bin/env python
# -*- coding: utf-8 -*-
################################################################################
#
# ConfigMgr configuration files generation wrapper
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
Generators for the Vigilo Config Manager


"""
import glob
import os, sys
import os.path
import types

from pkg_resources import working_set

from ..lib.generators import Generator
from ..lib.generators.file import FileGenerator
from ..lib.generators.map import MapGenerator

from vigilo.common.conf import settings

class GeneratorManager(object):
    """
    Handles the generator library.
    @cvar genclasses: the list of available generators.
    @type genclasses: C{list}
    """

    genshi_enabled = False

    def __init__(self):
        try:
            self.genshi_enabled = settings['vigiconf'].as_bool(
                                    'enable_genshi_generation')
        except KeyError:
            self.genshi_enabled = False

    def generate(self, h, v):
        """Execute each subclass' generate() method"""
        for entry in working_set.iter_entry_points("vigilo.vigiconf.generators"):
            genclass = entry.load()
            generator = genclass(h, v)
            generator.generate()


