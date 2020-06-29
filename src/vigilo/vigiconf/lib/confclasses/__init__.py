# -*- coding: utf-8 -*-
# Copyright (C) 2006-2020 CS GROUP – France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
This module contains the classes used in the configuration system.
"""

__all__ = [
    'get_text',
    'get_attrib',
]

def get_text(elem):
    """
    Renvoie le texte contenu dans une balise.

    Cette fonction respecte l'attribut "xml:space" :
    -   le texte est normalisé par défaut ou lorsque "xml:space" est
        explicitement positionné à "default"
    -   le texte est conservé intact lorsque "xml:space" vaut "preserve"

    @param elem: Élément dont on souhaite retourner le texte.
    @type elem: C{etree.ElementTree}
    @return: Le texte de l'élément, une fois la normalisation des blancs
        appliquée. Cette fonction considère qu'une balise auto-fermante
        ne contient pas de texte et renvoie None dans ce cas.
    @rtype: C{unicode} ou C{None}
    """
    space = elem.get('{http://www.w3.org/XML/1998/namespace}space', 'default')
    if elem.text is None:
        return None

    if space == 'preserve':
        # On renvoie une chaîne de type Unicode (cf. signature de la fonction),
        # même si cela à un impact sur les performances sous Python 2,
        # Voir https://lxml.de/3.6/FAQ.html#why-does-lxml-sometimes-return-str-values-for-text-in-python-2
        # pour plus d'information.
        typ = type(u'')
        return typ(elem.text)

    # Par défaut, split() coupe sur n'importe quel caractère blanc
    # et supprime les chaînes vides (ie. successions de caractères blancs),
    # ce qui correspond précisément à la normalisation souhaitée.
    return u' '.join(elem.text.split())


def get_attrib(elem, attr):
    """
    Renvoie la valeur d'un attribut de l'élément.

    @param elem: Élément dont on souhaite retourner un attribut.
    @type elem: C{etree.ElementTree}
    @param attr: Nom de l'attribut à retourner sur cet élément.
    @type attr: C{basestr}
    @return: La valeur de l'attribut L{attr} de l'élément L{elem}
        ou None si l'attribut n'existe pas.
    @rtype: C{unicode} ou C{None}
    """
    try:
        attrib = elem.attrib[attr]
    except KeyError:
        return None

    # La normalisation des valeurs des attributs est un peu bancale
    # dans la spécification de XML :
    # - tous les blancs sont remplacés par des espaces
    # - les références et entités sont remplacées récursivement
    #   par les caractères correspondant
    # - les successions de blancs sont remplacées par un seul espace
    #   et les blancs en début/fin de valeur sont supprimés,
    #   MAIS UNIQUEMENT lorsque la valeur est d'un type différent
    #   de CDATA dans la DTD du document.
    #
    # Par souci de cohérence, on émule le fonctionnement de la dernière
    # règle pour tous les types.
    return u' '.join(attrib.split())
