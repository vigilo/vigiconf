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
Data loaders for models like HostGroup, ServiceGroup, Dependency.

File format: XML
Notice: some other models like Host have their own loader (confclasses)
TODO: confclasses refactoring needed ?
"""
import os
import subprocess

from xml.etree import ElementTree as ET # Python 2.5

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from .. import conf

from ..lib import ParsingError

__docformat__ = "epytext"

class XMLLoader:
    """ Classe abstraite de chargement des données XML de la configuration.
    
    La méthode load doit être redéfinie obligatoirement.
    
    Caractéristiques:
    - chargement de données XML dans une hiérarchie de répertoires
    - exclusion de certains répertoires
    - validation XSD 
    """
    
    _xsd_dir = os.path.join(os.path.dirname(__file__),
                            '..', "validation", "xsd")
    _xsd_file_path = None
    _xsd_filename = None
    
    do_validation = True
    
    def __init__(self, xsd_filename=None):
        if xsd_filename: self._xsd_filename = xsd_filename
        if self._xsd_filename:
            self._xsd_file_path = os.path.join(self._xsd_dir,
                                               self._xsd_filename)
    
    def load(self, path):
        """ Charge des données depuis un fichier xml.
        
        Cette méthode doit redéfinie dans une classe dérivée
        
            @param filepath: an XML file
            @type  filepath: C{str}
        """
        raise Exception("should be implemented in a subclass")
    
    def validate(self, xmlfile):
        """
        Validate the XML against the XSD using xmllint
        
        @note: this could take time.
        @todo: use lxml for python-based validation
        @param xmlfile: an XML file
        @type  xmlfile: C{str}
        @param  xsdfilename: an XSD file name (present in the validation/xsd dir)
        @type  xsdfilename: C{str}
        """
        xsd = self._xsd_file_path
        result = subprocess.call(["xmllint", "--noout", "--schema", xsd, xmlfile])
        if result != 0:
            raise ParsingError("XML validation failed (%s/%s)" % (xmlfile, xsd))
    
    def visit_dir(self, dirname):
        """
        @return True if dirname should be visited to load data
        """
        if dirname.startswith("."):
            return False
        if dirname == "CVS":
            return False
        
        return True

    def load_dir(self, basedir):
        """ Generic loader of data from xml files.
        
            @param basedir: a directory containing xml files
            @type  basedir: C{str}
        """
        for root, dirs, files in os.walk(basedir):
            for f in files:
                if not f.endswith(".xml"):
                    continue
                path = os.path.join(root, f)
                if self.do_validation:
                    if self._xsd_file_path:
                        self.validate(path)
                    else:
                        raise Exception("A XSD Schema should be provided.")
                # load data
                self.load(path)
            
                LOGGER.debug("Sucessfully parsed %s" % path)
                
            for d in dirs: # Don't visit subversion/CVS directories
                if not self.visit_dir(d):
                    dirs.remove(d)

