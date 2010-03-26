#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generators for the Vigilo Config Manager
"""

from __future__ import absolute_import

import glob
import sys
import os
import os.path
import shutil
import types

from vigilo.common.conf import settings

from .. import conf

class Templator(object):
    """
    The base class for the generators
    
    TODO: refactoring: utiliser le template engine Genshi ?
    
    @ivar mapping: ventilation mapping
    @type mapping: C{dict}, see the L{lib.ventilator.findAServerForEachHost}()
        function
    @ivar baseDir: generation directory
    @type baseDir: C{str}
    @ivar validator: validator instance for warnings and errors
    @type validator: L{Validator<lib.validator.Validator>}
    @ivar openFiles: cache of the open template files
    @type openFiles: C{dict}
    @ivar prettyName: pretty name for this generator
    @type prettyName: C{str}
    """

    COMMON_PERL_LIB_FOOTER = "1;\n"

    def __init__(self, gendir, mapping, validator):
        self.mapping = mapping
        self.baseDir = gendir
        self.validator = validator
        self.openFiles = {}
        self.prettyName = str(self.__class__.__name__)
        self.prettyName = self.prettyName.replace("__main__.","")
        self.prettyName = self.prettyName.replace("Tpl","")
        validator.addAGenerator()

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

    def addWarning(self, element, msg):
        """
        Add a warning in the validator
        @param element: the element emitting the warning (usually a host)
        @type  element: C{str}
        @param msg: the warning message
        @type  msg: C{str}
        """
        self.validator.addWarning(self.prettyName, element, msg)

    def addError(self, element, msg):
        """
        Add a error in the validator
        @param element: the element emitting the error (usually a host)
        @type  element: C{str}
        @param msg: the error message
        @type  msg: C{str}
        """
        self.validator.addError(self.prettyName, element, msg)

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

    def generate(self):
        """
        The main generation method.
        @note: To be reimplemented by sub-classes
        """
        pass


class GeneratorManager(object):
    """
    Handles the generator library.
    @cvar genclasses: the list of available generators.
    @type genclasses: C{list}
    """

    genclasses = []

    def __init__(self):
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
                if issubclass(genclass, View) and  name != "View":
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


# new template engine (genshi)
from genshi.template import TextTemplate
from genshi.template import TemplateLoader

class View:
    """
    The base class for the generators (Genshi template engine)
    
    @ivar mapping: ventilation mapping
    @type mapping: C{dict}, see the L{lib.ventilator.findAServerForEachHost}()
        function
    @ivar baseDir: generation directory
    @type baseDir: C{str}
    @ivar validator: validator instance for warnings and errors
    @type validator: L{Validator<lib.validator.Validator>}
    """
    
    def __init__(self, gendir, mapping={}, validator=None, template_dir=None):
        self.mapping = mapping
        self.baseDir = gendir
        
        if not template_dir:
            template_dir = os.path.join(settings["vigiconf"].get("confdir"),
                                      "filetemplates")
        self.loader = TemplateLoader(template_dir, auto_reload=False)

    def create_dir_if_missing(self, filename):
        """
        Creates all directories on the path of the provided filename
        @param filename: a file path
        @type  filename: C{str}
        """
        destdir = os.path.dirname(filename)
        if destdir != "" and not os.path.exists(destdir):
            os.makedirs(destdir)
    
    def reventilate(self, app_key, apps):
        """ reventile le mapping ventilation.
        """
        servers = {}
        
        for ventilation in self.mapping.values():
            if app_key not in ventilation :
                continue
            for i in apps:
                if i in ventilation:
                    app_server = ventilation[app_key]
                    
                    if not servers.has_key(app_server):
                        servers[app_server] = []
                    if ventilation[i] not in servers[app_server]:
                        servers[app_server].append(ventilation[i])
        return servers
        
        
    def render(self, template, context, filename=None):
        """ génération de texte à partir d'un template genshi.
        
        """
        tmpl = self.loader.load(template, cls=TextTemplate)
        stream = tmpl.generate(**context)
        print context
        if not filename:
            return stream.render()
        
        self.create_dir_if_missing(filename)
        
        fout = open(os.path.join(self.baseDir, filename), "w")
        fout.write(stream.render())
        fout.close()


# vim:set expandtab tabstop=4 shiftwidth=4:
