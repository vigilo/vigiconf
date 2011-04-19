# -*- coding: utf-8 -*-
# Copyright (C) 2006-2011 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
This module contains the classes used in the configuration system.
"""

from vigilo.common import parse_path

__all__ = [
    'get_text',
    'get_attrib',
    'parse_path',
]

def get_text(elem):
    """
    Renvoie le texte contenu dans une balise.

    @param elem: Élément dont on souhaite retourner le texte.
    @type elem: C{etree.ElementTree}
    @return: Le texte de l'élément ou None s'il n'y en a pas
        ou si l'élément ne contient que des caractères blancs.
    @rtype: C{unicode} ou C{None}
    """
    if not elem.text or not elem.text.strip():
        return None
    return elem.text

def get_attrib(elem, attr):
    """
    Renvoie la valeur d'un attribut de l'élément.

    @param elem: Élément dont on souhaite retourner un attribut.
    @type elem: C{etree.ElementTree}
    @param attr: Nom de l'attribut à retourner sur cet élément.
    @type attr: C{basestr}
    @return: La valeur de l'attribut L{attr} de l'élément L{elem} ou None
        si l'attribut n'existe pas ou ne contient que des caractères blancs.
    @rtype: C{unicode} ou C{None}
    """
    try:
        attrib = elem.attrib[attr]
    except KeyError:
        return None
    else:
        if not attrib or not attrib.strip():
            return None
        return attrib
