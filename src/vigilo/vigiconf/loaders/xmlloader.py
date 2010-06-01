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
Data loaders for models like SupItemGroup, Dependency.

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
    
    _unit_filename = "final.xml"
    
    # current bloc list (ie. ['nodes', 'node', 'item'])
    _bloclist = []
    # current element
    _elem = None
    
    do_validation = True
    
    # change detection
    change = False
    # gestion de la suppression des entités
    dbupdater = None
    
    def __init__(self, xsd_filename=None):
        """ Constructeur.
        @param  xsd_filename: an XSD file name (present in the validation/xsd dir)
        @type  xsd_filename: C{str}
        """
        
        if xsd_filename: self._xsd_filename = xsd_filename
        if self._xsd_filename:
            self._xsd_file_path = os.path.join(self._xsd_dir,
                                               self._xsd_filename)
    
    def load(self, path):
        """ Charge des données depuis un fichier xml.
        
        Cette méthode peut être redéfinie dans une classe dérivée.
        L'implémentation par défaut (méthode parse) nécessite d'implémenter dans la
        classe dérivée les méthodes start_element et end_element.
        
        @param path: an XML file
        @type  path: C{str}
        """
        if self.dbupdater:
            self.dbupdater.load_instances()
        
        self.parse(path)
        
        if self.dbupdater:
            self.dbupdater.update()
    
    def validate(self, xmlfile):
        """
        Validate the XML against the XSD using xmllint
        
        @note: this could take time.
        @todo: use lxml for python-based validation
        @param xmlfile: an XML file
        @type  xmlfile: C{str}
        """
        xsd = self._xsd_file_path
        devnull = open("/dev/null", "w")
        result = subprocess.call(["xmllint", "--noout", "--schema", xsd, xmlfile],
                    stdout=devnull, stderr=subprocess.STDOUT)
        devnull.close()
        if result != 0:
            raise ParsingError("XML validation failed (%s/%s)" % (xmlfile, xsd))
    
    def visit_dir(self, dirname):
        """ validate the exploration of a directory.
        
        @param dirname: a directory name
        @type  dirname: C{str}
        @return:  True if dirname should be visited to load data
        @rtype: C{boolean}
        """
        if dirname.startswith("."):
            return False
        if dirname == "CVS":
            return False
        
        return True
    
    def get_xml_parser(self, path, events=("start", "end")):
        """ get an XML parser.
        
        Usage::
        for event, elem in self.get_xml_parser(filepath):
            if event == "start":
                if elem.tag == "map":
                    # DO SOMETHING
        
        @param path: an XML file
        @type  path: C{str}
        @param events: list of events. default=('start', 'end')
        @type  events: C{seq}
        """
        return ET.iterparse(path, events=("start", "end"))
    
    def parse(self, path):
        """ Default parser.
        
        The XMLLoader subclass should implement  the 2 methods:
          - start_element(tag)
          - end_element(tag)
        
        and should use the following methods:
          - get_attrib(name)
          - get_text()
        
        @param path: an XML file
        @type  path: C{str}
        """
        for event, elem in self.get_xml_parser(path, ("start", "end")):
            self._elem = elem
            if event == "start":
                self._bloclist.append(elem.tag)
                
                self.start_element(elem.tag)
            elif event == "end":
                self.end_element(elem.tag)
                
                start_tag = self._bloclist.pop()
                if start_tag != elem.tag:
                    raise Exception("End tag mismatch error: %s/%s" % (start_tag, elem.tag))
    
    def start_element(self, tag):
        """ should be implemented by the subclass when using parse method
        
        Does nothing
        
        one should use the following methods:
          - get_attrib(name)
          - get_text()
        
        and attributes
          - _bloclist that contains current bloc hierarchy
          ie. ['nodes', 'node', 'item']
        
        @param tag: an XML tag
        @type  tag: C{str}
        """
        pass
    
    def end_element(self, tag):
        """ should be implemented by the subclass when using parse method
        
        Does nothing
        
        one should use the following methods:
          - get_attrib(name)
          - get_text()
        
        and attributes
          - _bloclist that contains current bloc hierarchy
          ie. ['nodes', 'node', 'item']
        
        @param tag: an XML tag
        @type  tag: C{str}
        """
        pass
    
    def get_text(self, elem=None):
        """ Obtient le bloc texte entre deux tags XML.
        
        Les blancs début et fin sont retirés.
        
        @param elem: élément (élément courant par défaut)
        @type  elem: C{object}
        """
        if elem == None: elem = self._elem
        return elem.text.strip()
    
    def get_attrib(self, name, elem=None):
        """ Obtient la valeur d'un attribut XML.
        
        Les blancs début et fin sont retirés.
        @param name: nom de l'attribut
        @type  name: C{str}
        @param elem: élément (élément courant par défaut)
        @type  elem: C{object}
        """
        if elem == None: elem = self._elem
        return elem.attrib[name].strip()

    def get_utext(self, elem=None):
        """ Obtient le bloc texte unicode entre deux tags XML.
        
        Les blancs début et fin sont retirés.
        @param elem: élément (élément courant par défaut)
        @type  elem: C{object}
        """
        return unicode(self.get_text(elem))
    
    def get_uattrib(self, name, elem=None):
        """ Obtient la valeur d'un attribut XML en unicode.
        
        Les blancs début et fin sont retirés.
        @param name: nom de l'attribut
        @type  name: C{str}
        @param elem: élément (élément courant par défaut)
        @type  elem: C{object}
        """
        return unicode(self.get_attrib(name, elem))
    
    def delete_all(self):
        """ efface la totalité des entités de la base
        
        méthode à redéfinir dans la classe héritière.
        """
        raise Exception("not implemented.")
    
    def reset_change(self):
        """ Initialisation de la séquence de détection de changement.
        
        met à jour l'attribut booléen change à False.
        """
        self.change = False
    
    def detect_change(self):
        """ détecte un éventuel changement.
        
        méthode à redéfinir dans la classe héritière.
        
        @return: True si changement détecté
        """
        raise Exception("not implemented.")
        
    def load_dir(self, basedir, delete_all=False):
        """ Chargement de données dans une hiérarchie de fichiers XML.
        
            Dans chaque répertoire, un fichier spécifique self._unit_filename
            nommé par défaut "final.xml" est chargé en dernier, ce qui permet
            de faire des mises à jour unitaires en ajoutant un tel
            fichier (qui peut contenir par exemple la suppression d'un élément)
        
            --------------------------------------
            VIGILO_EXIG_VIGILO_CONFIGURATION_0030
            Interface programmatique de configuration.
            
            Les modes de configuration sont les suivants :
              - mise à jour de la totalité de la configuration via l'interface
                programmatique pour l'ensemble des configurations
              - mise à jour unitaire d'un élément de la configuration via
                l'interface programmatique
            --------------------------------------
        
            @param basedir: a directory containing xml files
            @type  basedir: C{str}
            @param delete_all: delete all entities before loading (default)
            @type delete_all: C{boolean}
        """
        
        if  delete_all:
            self.delete_all()
        
        for root, dirs, files in os.walk(basedir):
            final = False
            
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
                if f == self._unit_filename:
                    final = True
                else:
                    self.load(path)
                
                LOGGER.debug("Sucessfully parsed %s" % path)
            
            # parsing du dernier fichier à traiter pour des mises
            # à jour unitaires
            if final:
                self.load(self._unit_filename)
                
            for d in dirs: # Don't visit subversion/CVS directories
                if not self.visit_dir(d):
                    dirs.remove(d)

