# -*- coding: utf-8 -*-
################################################################################
#
# ConfigMgr Nagios Collector plugin configuration file generator
# Copyright (C) 2007-2015 CS-SI
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

import os
import os.path
import shutil

from pkg_resources import resource_listdir, resource_string, \
        resource_stream, resource_exists

from vigilo.common.conf import settings

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

from .base import Generator


__all__ = ("FileGenerator",)


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

    def __init__(self, application, ventilation):
        super(FileGenerator, self).__init__(application, ventilation)
        self.override_path = os.path.join(
                                settings["vigiconf"].get("confdir"),
                                "filetemplates", self.application.name)
        self.openFiles = {}
        self.templates = self.loadTemplates()
        self.results["files"] = 0
        self.results["dirs"] = 0

    def generate_host(self, hostname, vserver):
        raise NotImplementedError()

    def copy(self, tplsrc, dst):
        """
        Simply copy a file to a destination, creating directories if necessary.
        @param tplsrc: origin, in the templates folder
        @type  tplsrc: C{str}
        @param dst: destination
        @type  dst: C{str}
        """
        dstdir = os.path.dirname(dst)
        try:
            os.makedirs(dstdir)
        except OSError:
            pass
        if os.path.exists(os.path.join(self.override_path, tplsrc)):
            LOGGER.debug("Using overridden template from %s"
                         % os.path.join(self.override_path, tplsrc))
            shutil.copyfile(os.path.join(self.override_path, tplsrc), dst)
            return
        if not resource_exists(self.application.__module__,
                    "templates/%s" % tplsrc):
            self.addError(self.application.name,
                                    _("No such template: %s") % tplsrc)
            return
        src = resource_stream(self.application.__module__,
                    "templates/%s" % tplsrc)
        dst_file = open(dst, "w")
        dst_file.write(src.read())
        dst_file.close()
        src.close()

    def createDirIfMissing(self, filename):
        """
        Creates all directories on the path of the provided filename
        @param filename: a file path
        @type  filename: C{str}
        """
        destdir = os.path.dirname(filename)
        try:
            os.makedirs(destdir)
            self.results["dirs"] += 1
        except OSError:
            pass

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
        self.openFiles[filename].write((template % args).encode('utf8'))

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
        self.results["files"] += 1
        self.createDirIfMissing(filename)
        self.openFiles[filename] = open(filename,"w")
        self.templateAppend(filename, template, args)

    def loadTemplates(self):
        """
        Load the templates available in the configuration for the application.
        """
        if not resource_exists(self.application.__module__, "templates"):
            return {}
        templates = {}
        for filename in resource_listdir(self.application.__module__,
                                         "templates"):
            if not filename.endswith(".tpl"):
                continue
            tplname = filename[:-4]
            if os.path.exists(os.path.join(self.override_path, filename)):
                LOGGER.debug("Using overridden template from %s"
                             % os.path.join(self.override_path, filename))
                t = open(os.path.join(self.override_path, filename))
                tpl = t.read()
                t.close()
            else:
                tpl = resource_string(self.application.__module__,
                            "templates/%s" % filename)
            templates[tplname] = tpl
        return templates

    def quote(self, s):
        """
        Permet l'échappement des chaîne de caractères en vue de l'inclure
        dans un template dans une valeur de type chaîne de caractère entourée
        de quotes simples <'>.
        @param s: La chaîne de caractères à échapper.
        @type  s: C{basestring}
        @return: La chaîne résultat.
        @rtype: C{basestring}

        """
        return s.replace("\\", "\\\\").replace("'", "\\'")
