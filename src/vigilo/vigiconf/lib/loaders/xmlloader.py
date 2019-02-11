# -*- coding: utf-8 -*-
# Copyright (C) 2007-2019 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>
"""
Data loaders for models like SupItemGroup, Dependency.

File format: XML
Notice: some other models like Host have their own loader (confclasses)
TODO: confclasses refactoring needed ?
"""

from __future__ import absolute_import

import os
from lxml import etree

from pkg_resources import resource_filename

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

from vigilo.models.session import DBSession
from vigilo.models.tables import SupItem

from .dbloader import DBLoader
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


    def get_xsd_path(self):
        if not self._xsd_filename:
            return None
        return resource_filename("vigilo.vigiconf",
                    "validation/xsd/%s" % self._xsd_filename)

    def get_xsd(self):
        if not self._xsd_filename:
            return None
        xsd_path = self.get_xsd_path()
        if not os.path.exists(xsd_path):
            raise OSError(_("XSD file does not exist: %s") % xsd_path)
        try:
            xsd_doc = etree.parse(xsd_path)
            xsd = etree.XMLSchema(xsd_doc)
        except (etree.XMLSyntaxError, etree.XMLSchemaParseError) as e:
            raise ParsingError(_("Invalid XML validation schema %(schema)s: "
                                "%(error)s") % {
                                    'schema': xsd_path,
                                    'error': str(e),
                                })
        except IOError as e:
            raise ParsingError(_("Error reading %(file)s, make sure the "
                                 "permissions are set correctly."
                                 "Message: %(error)s.") % {
                                    'file': xsd_path,
                                    'error': str(e),
                                })
        return xsd

    def validate(self, xmlfile, xsd): # pylint: disable-msg=R0201
        """
        Validate the XML against the XSD using lxml
        @param xmlfile: an XML file
        @type  xmlfile: C{str}
        """
        try:
            source_doc = etree.parse(xmlfile)
        except etree.XMLSyntaxError as e:
            raise ParsingError(_("XML syntax error in %(file)s: %(error)s") %
                               { 'file': xmlfile, 'error': str(e) })
        except IOError as e:
            raise ParsingError(_("Error reading %(file)s, make sure the "
                                 "permissions are set correctly."
                                 "Message: %(error)s.") % {
                                    'file': xmlfile,
                                    'error': str(e),
                                })
        valid = xsd.validate(source_doc)
        if not valid:
            raise ParsingError(_("XML validation failed: %(error)s") % {
                                    'error': xsd.error_log.last_error,
                                })
        return source_doc

    def visit_dir(self, dirname): # pylint: disable-msg=R0201
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

    def load_file(self, path, xml=None):
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
            if xml is not None:
                iterator = etree.iterwalk
                source = xml
            else:
                iterator = etree.iterparse
                source = path
            for event, elem in iterator(source, ("start", "end")):
                self._elem = elem
                if event == "start":
                    self._bloclist.append(elem.tag)

                    self.start_element(elem)
                elif event == "end":
                    self.end_element(elem)

                    start_tag = self._bloclist.pop()
                    if start_tag != elem.tag:
                        raise ParsingError(_("End tag mismatch error: "
                                            "%(start)s/%(end)s") % {
                            'start': start_tag,
                            'end': elem.tag,
                        })
            DBSession.flush()
        except ParsingError as e:
            raise ParsingError(_('Syntax error in "%(path)s": %(error)s') % {
                'path': path,
                'error': e,
            })

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

        @param elem: élément (élément courant par défaut)
        @type  elem: C{object}
        """
        if elem == None:
            elem = self._elem
        return elem.text

    def get_attrib(self, name, elem=None):
        """ Obtient la valeur d'un attribut XML.

        @param name: nom de l'attribut
        @type  name: C{str}
        @param elem: élément (élément courant par défaut)
        @type  elem: C{object}
        """
        if elem == None:
            elem = self._elem
        return elem.attrib[name]

    def get_utext(self, elem=None):
        """ Obtient le bloc texte unicode entre deux tags XML.

        @param elem: élément (élément courant par défaut)
        @type  elem: C{object}
        """
        res = self.get_text(elem)
        if res is None:
            return None
        return unicode(res)

    def get_uattrib(self, name, elem=None):
        """ Obtient la valeur d'un attribut XML en unicode.

        @param name: nom de l'attribut
        @type  name: C{str}
        @param elem: élément (élément courant par défaut)
        @type  elem: C{object}
        """
        res = self.get_attrib(name, elem)
        if res is None:
            return None
        return unicode(res)

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

        if self.do_validation:
            xsd = self.get_xsd()
        for root, dirs, files in os.walk(basedir):
            final = False

            for f in files:
                if not f.endswith(".xml"):
                    continue
                path = os.path.join(root, f)
                if self.do_validation:
                    fxml = self.validate(path, xsd)
                else:
                    fxml = None
                # load data
                if f == self._unit_filename:
                    final = True
                else:
                    self.load_file(path, fxml)
                    LOGGER.debug("Successfully parsed %s", path)

            # parsing du dernier fichier à traiter pour des mises
            # à jour unitaires
            if final:
                self.load_file(self._unit_filename)

            for d in dirs: # Don't visit subversion/CVS directories
                if not self.visit_dir(d):
                    dirs.remove(d)

    # Fonctions utilitaires
    def get_supitem(self, elem):
        supitem = None
        host = None
        service = None
        if "host" in elem.attrib:
            host = self.get_uattrib("host", elem)
        if "service" in elem.attrib:
            service = self.get_uattrib("service", elem)

        # @TODO: il faudrait fusionner le get_supitem() et la requête d'après.
        supitem = SupItem.get_supitem(host, service)
        if supitem is None:
            raise ParsingError(_("Can't find an item matching %s") %
                repr(elem.attrib))
        return DBSession.query(SupItem).get(supitem)
