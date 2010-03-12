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

from vigilo.models.configure import DBSession

from vigilo.models import HostGroup, ServiceGroup
from vigilo.models import Host, LowLevelService, HighLevelService, Dependency

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
        self._xsd_file_path = os.path.join(self._xsd_dir, self._xsd_filename)
    
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


def load_hlservices(basedir):
    """ Loads dependencies from xml files.
    
        @param basedir: a directory containing dependency definitions files
        @type  basedir: C{str}
    """
    _load_from_xmlfiles(basedir, "hlservice.xsd", _load_hlservices_from_xml)


def _load_from_xmlfiles(basedir, xsd_file, handler):
    """ Generic loader of data from xml files.
    
        @param basedir: a directory containing xml files
        @type  basedir: C{str}
        @param xsd_file: a xsd file for validation
        @type  xsd_file: C{str}
        @param handler:  a processing function for a xml file with one argument (path)
        @type  handler: C{function}
    """
    for root, dirs, files in os.walk(basedir):
        for f in files:
            if not f.endswith(".xml"):
                continue
            path = os.path.join(root, f)
            _validate(path, xsd_file)
            # load data
            handler(path)
        
            LOGGER.debug("Sucessfully parsed %s" % path)
        for d in dirs: # Don't visit subversion/CVS directories
            if d.startswith("."):
                dirs.remove(d)
            if d == "CVS":
                dirs.remove("CVS")


def _validate(xmlfile, xsdfilename):
    """
    Validate the XML against the DTD using xmllint
    
    @note: this could take time.
    @todo: use lxml for python-based validation
    @param xmlfile: an XML file
    @type  xmlfile: C{str}
    @param  xsdfilename: an XSD file name (present in the validation/xsd dir)
    @type  xsdfilename: C{str}
    """
    xsd = os.path.join(os.path.dirname(__file__), '..',
                       "validation", "xsd", xsdfilename)
    result = subprocess.call(["xmllint", "--noout", "--schema", xsd, xmlfile])
    if result != 0:
        raise ParsingError("XML validation failed (%s/%s)" % (xmlfile, xsd))


def _load_hlservices_from_xml(filepath):
    """ Loads high level services from a xml file.
    
        @param filepath: an XML file
        @type  filepath: C{str}
    """
    deleting_mode = False
    
    try:
        for event, elem in ET.iterparse(filepath, events=("start", "end")):
            if event == "start":
                if elem.tag == "hlservice":
                    name = elem.attrib["name"].strip()
                    groups = []
                    message = None
                elif elem.tag == "message":
                    message = elem.text
                elif elem.tag == "warning_threshold":
                    warning_threshold = int(elem.attrib["value"].strip())
                elif elem.tag == "critical_threshold":
                    critical_threshold = int(elem.attrib["value"].strip())
                elif elem.tag == "priority":
                    priority = int(elem.attrib["value"].strip())
                elif elem.tag == "op_dep":
                    op_dep = elem.attrib["value"].strip()
                elif elem.tag == "group":
                    group = elem.attrib["name"].strip()
                    groups.append(group)
                elif elem.tag == "todelete":
                    deleting_mode = True
            else:
                if elem.tag == "hlservice":
                    # on instancie ou on récupère le HLS
                    hls = HighLevelService.by_service_name(name)
                    if hls:
                        if deleting_mode:
                            DBSession.delete(hls)
                            continue
                        
                        hls.servicename = unicode(name)
                        hls.op_dep = unicode(op_dep)
                        hls.message = unicode(message)
                        hls.priority = priority
                        hls.warning_threshold = warning_threshold
                        hls.critical_threshold = critical_threshold
                    else:
                        hls = HighLevelService(servicename=unicode(name),
                                       op_dep=unicode(op_dep),
                                       message=unicode(message),
                                       priority=priority,
                                       warning_threshold=warning_threshold,
                                       critical_threshold=critical_threshold
                                               )
                        DBSession.add(hls)
                    # ajout des groupes
                    hls.groups = []
                    for gname in groups:
                        sg = ServiceGroup.by_group_name(gname)
                        if not sg:
                            raise Exception("Service group %s does not exist."
                                            % gname)
                        hls.groups.append(sg)
                elif elem.tag == "todelete":
                    deleting_mode = False
                    
                    # ajout des impacts
                    # les impacts sont ajoutés après le traitement de
                    # l'ensemble des fichiers
                    
        DBSession.flush()
    except:
        #DBSession.rollback()
        raise

