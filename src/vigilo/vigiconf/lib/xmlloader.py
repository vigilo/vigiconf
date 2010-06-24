# -*- coding: utf-8 -*-
################################################################################
#
# VigiConf configuration files generation wrapper
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
from xml.etree import ElementTree as ET # Python >= 2.5

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.models.session import DBSession

from vigilo.vigiconf.lib.dbloader import DBLoader
from vigilo.vigiconf.lib import ParsingError

__docformat__ = "epytext"

class XMLLoader(DBLoader):
    """ Classe abstraite de chargement des données XML de la configuration.
    
    La méthode load doit être redéfinie obligatoirement.
    
    Caractéristiques:
      - chargement de données XML dans une hiérarchie de répertoires
      - exclusion de certains répertoires
      - validation XSD 

    Le parsing est basé sur SAX plutôt que sur DOM pour des questions de
    performances : on peut très bien avoir plusieurs dizaines de milliers
    d'hôtes dans le même fichier XML.

    @ivar  _xsd_filename: an XSD file name (present in the validation/xsd dir)
    @type  _xsd_filename: C{str}
    """
    
    _xsd_filename = None
    _unit_filename = "final.xml"
    
    def __init__(self, cls, key_attr=None):
        super(XMLLoader, self).__init__(cls, key_attr)
        # current bloc list (ie. ['nodes', 'node', 'item'])
        self._bloclist = []
        # current element
        self._elem = None
        self.do_validation = True
        # change detection
        self.change = False
    

    def get_xsd_file(self):
        if not self._xsd_filename:
            return None
        # TODO: utiliser pkg_resources pour pouvoir fonctionner en mode egg
        xsd_dir = os.path.join(os.path.dirname(__file__),
                               '..', "validation", "xsd")
        return os.path.join(xsd_dir, self._xsd_filename)

    def validate(self, xmlfile):
        """
        Validate the XML against the XSD using xmllint
        
        @note: this could take time.
        @todo: use lxml for python-based validation
        @param xmlfile: an XML file
        @type  xmlfile: C{str}
        """
        xsd = self.get_xsd_file()
        if not xsd:
            raise ValueError("An XSD schema should be provided for validation.")
        if not os.path.exists(xsd):
            raise OSError("XSD file does not exist: %s" % xsd)

        devnull = open("/dev/null", "w")
        # TODO: validation avec lxml plutôt que xmllint ?
        result = subprocess.call(
                    ["xmllint", "--noout", "--schema", xsd, xmlfile],
                    stdout=devnull, stderr=subprocess.STDOUT)
        devnull.close()
        if result != 0:
            raise ParsingError("XML validation failed (%s/%s)"
                               % (xmlfile, xsd))
    
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
    

    def load_file(self, path):
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
        try:
            for event, elem in self.get_xml_parser(path, ("start", "end")):
                self._elem = elem
                if event == "start":
                    self._bloclist.append(elem.tag)
                    
                    self.start_element(elem)
                elif event == "end":
                    self.end_element(elem)
                    
                    start_tag = self._bloclist.pop()
                    if start_tag != elem.tag:
                        raise ParsingError("End tag mismatch error: %s/%s"
                                        % (start_tag, elem.tag))
            DBSession.flush()
        except ParsingError, e:
            raise ParsingError("Syntax error in \"%s\": %s" % (path, e))
    
    def start_element(self, tag):
        """ should be implemented by the subclass when using load_file method
        
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
        """ should be implemented by the subclass when using load_file method
        
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
        raise NotImplementedError()
    
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
        raise NotImplementedError()
        
    def load_dir(self, basedir):
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
        """

        for root, dirs, files in os.walk(basedir):
            final = False
            
            for f in files:
                if not f.endswith(".xml"):
                    continue
                path = os.path.join(root, f)
                if self.do_validation:
                    self.validate(path)
                # load data
                if f == self._unit_filename:
                    final = True
                else:
                    self.load_file(path)
                    LOGGER.debug("Sucessfully parsed %s" % path)
            
            # parsing du dernier fichier à traiter pour des mises
            # à jour unitaires
            if final:
                self.load_file(self._unit_filename)
                
            for d in dirs: # Don't visit subversion/CVS directories
                if not self.visit_dir(d):
                    dirs.remove(d)

