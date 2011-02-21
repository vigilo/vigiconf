# -*- coding: utf-8 -*-
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

def parse_path(path):
    """
    Analyse le contenu d'un chemin d'accès et retourne
    une liste de ses composantes.

    @param path: Chemin d'accès relatif ou absolu.
    @type path: C{basestr}
    @return: Ensemble des composantes du chemin d'accès
        ou None si L{path} ne représente pas un chemin
        d'accès valide.
    @rtype: C{set} ou C{None}
    """
    parts = []

    # On refuse les chemins d'accès vides.
    if not path:
        return None

    absolute = (path[0] == '/')
    if absolute:
        path = path[1:]
    it = iter(path)

    try:
        portion = ""
        while True:
            ch = it.next()
            # Il s'agit d'une séquence d'échappement.
            if ch == '\\':
                ch = it.next()
                # Les seules séquences reconnues sont "\\" et "\/"
                # pour échapper le caractère d'échappement et le
                # séparateur des composantes du chemin respectivement.
                if ch == '/' or ch == '\\':
                    portion += ch
                else:
                    return None
            # Il s'agit d'un séparateur de chemins.
            elif ch == '/':
                if not portion:
                    return None
                parts.append(portion)
                portion = ""
            # Il s'agit d'un autre caractère (quelconque).
            else:
                portion += ch
    except StopIteration:
        if portion:
            parts.append(portion)

    # Permet de traiter correctement
    # le cas où le chemin est '/'.
    if not parts:
        return None

    # Un chemin relatif ne peut pas
    # contenir plusieurs composantes.
    if len(parts) != 1 and (not absolute):
        return None

    return parts
