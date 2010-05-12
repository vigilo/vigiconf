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
new template engine (genshi)

"""
import os
import os.path

from genshi.template import TextTemplate
from genshi.template import TemplateLoader

from vigilo.common.conf import settings

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
    
    def get_hosts_by_server(self, app_key):
        """
        """
        servers = {}
        for (hostname, ventilation) in self.mapping.iteritems():
            if app_key not in ventilation:
                continue
            app_server = ventilation[app_key]
            fileName = "%s/%s/connector-metro.conf.py" \
                       % (self.baseDir, app_server)
            if not servers.has_key(app_server):
                servers[app_server] = []
            if hostname not in servers[app_server]:
                servers[app_server].append(hostname)
        return servers
        
        
    def render(self, template, context, filename=None):
        """ génération de texte à partir d'un template genshi.
        
        """
        tmpl = self.loader.load(template, cls=TextTemplate)
        stream = tmpl.generate(**context)
        #print context
        if not filename:
            return stream.render()
        
        filepath = os.path.join(self.baseDir, filename)
        self.create_dir_if_missing(filepath)
        
        fout = open(filepath, "w")
        fout.write(stream.render())
        fout.close()

