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

from __future__ import absolute_import

import glob
import os
import os.path
import shutil

from vigilo.common.conf import settings

from . import Generator

class FileGenerator(Generator):
    """
    La classe de base pour les générateurs qui produisent des fichiers
    
    TODO: refactoring: utiliser le template engine Genshi ou Mako ?
    voir http://genshi.edgewall.org/wiki/GenshiPerformance
    
    @ivar baseDir: répertoire de generation
    @type baseDir: C{str}
    @ivar openFiles: cache of the open template files
    @type openFiles: C{dict}
    """

    COMMON_PERL_LIB_FOOTER = "1;\n"

    def __init__(self, mapping, validator):
        super(FileGenerator, self).__init__(mapping, validator)
        self.baseDir = os.path.join(settings["vigiconf"].get("libdir"), "deploy")
        self.openFiles = {}

    def copyFile(self, src, dst):
        """
        Simply copy a file to a destination, creating directories if necessary.
        @param src: origin
        @type  src: C{str}
        @param dst: destination
        @type  dst: C{str}
        """
        dstdir = os.path.dirname(dst)
        if not os.path.exists(dstdir):
            os.makedirs(dstdir)
        shutil.copyfile(src, dst)

    def createDirIfMissing(self, filename):
        """
        Creates all directories on the path of the provided filename
        @param filename: a file path
        @type  filename: C{str}
        """
        destdir = os.path.dirname(filename)
        if not os.path.exists(destdir):
            os.makedirs(destdir)
            self.validator.addADir()

    def templateAppend(self, filename, template, args):
        """
        Append a string to a file
        @param filename: the path of the file to append to
        @type  filename: C{str}
        @param template: the string to append. May contain formatting items
        @type  template: C{str}
        @param args: the formatting elements, if needed
        @type  args: C{dict}
        """
        self.openFiles[filename].write(template % args)

    def templateClose(self, filename):
        """
        Closes a file
        @param filename: the file to close
        @type  filename: C{str}
        """
        self.openFiles[filename].close()
        del self.openFiles[filename]

    def templateCreate(self, filename, template, args):
        """
        Create a new template file
        @param filename: the path of the file to create
        @type  filename: C{str}
        @param template: the string to add. May contain formatting items
        @type  template: C{str}
        @param args: the formatting elements, if needed
        @type  args: C{dict}
        """
        self.validator.addAFile()
        self.createDirIfMissing(filename)
        self.openFiles[filename] = open(filename,"w")
        self.templateAppend(filename, template, args)

    def loadTemplates(self, subdir):
        """
        Load the templates available in the configuration for the subdir item.
        @param subdir: the subdir to look into. Usually, it's the generator's
            name.
        @type  subdir: C{str}
        """
        templates = {}
        templates_path = os.path.join(settings["vigiconf"].get("confdir"),
                                      "filetemplates", subdir)
        for tpl in glob.glob("%s/*.tpl" % templates_path):
            name = os.path.basename(tpl)[:-4]
            f = open(tpl, "r")
            templates[name] = f.read()
            f.close()
        return templates

