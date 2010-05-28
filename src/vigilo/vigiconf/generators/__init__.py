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

from ..lib.generators.templator import Templator

from vigilo.common.conf import settings

class GeneratorManager(object):
    """
    Handles the generator library.
    @cvar genclasses: the list of available generators.
    @type genclasses: C{list}
    """

    genclasses = []
    genshi_enabled = False

    def __init__(self):
        try:
            self.genshi_enabled = settings['vigiconf'].as_bool(
                                    'enable_genshi_generation')
        except KeyError:
            self.genshi_enabled = False

        if not self.genclasses:
            self.__load()

    def __load(self):
        """Load the available generators"""
        generator_files = glob.glob(os.path.join(
                                os.path.dirname(__file__), "*.py"))
        for filename in generator_files:
            if os.path.basename(filename).startswith("__"):
                continue
            try:
                execfile(filename, globals(), locals())
            except Exception, e:
                sys.stderr.write("Error while parsing %s: %s\n" \
                                 % (filename, str(e)))
                raise
        for name, genclass in locals().iteritems():
            if isinstance(genclass, (type, types.ClassType)):
                if issubclass(genclass, Templator) and  name != "Templator":
                    self.genclasses.append(genclass)
            elif isinstance(genclass, (type, types.ModuleType)) and \
                    name not in globals():
                # This is an import statement and we don't have it yet,
                # re-bind it here
                globals()[name] = genclass
                continue

    def generate(self, gendir, h, v):
        """Execute each subclass' generate() method"""
        for genclass in self.genclasses:
            generator = genclass(gendir, h, v)
            generator.generate()


