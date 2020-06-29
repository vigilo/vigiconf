# -*- coding: utf-8 -*-
# Copyright (C) 2007-2020 CS GROUP – France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
This module contains the RRD-specific classes
"""



class Cdef(object):
    """
    Indicateur de type CDEF: il est calculé à partir d'autres indicateurs. Voir
    la page de manuel "rrdgraph".
    """

    def __init__(self, name, cdef):
        """
        @param name: le nom du CDEF, pour utilisation interne. Attention, seul
            de l'ASCII est autorisé.
        @type  name: C{str}
        @param cdef: la formule de calcul (en notation polonaise inversée).
            Peut contenir le nom d'autres I{DataSources}, qui seront remplacées
            par leur valeur à l'affichage.
        @type  cdef: C{str}
        """
        self.name = name.encode("ascii") # ASCII-only
        if isinstance(cdef, basestring):
            cdef = cdef.split(",")
        self.cdef = cdef

    def __str__(self):
        return self.name

    def to_dict(self):
        return {
            "name": self.name,
            "cdef": ",".join(self.cdef)
        }


class Graph(object):
    """
    This class defines the Graph configuration objects.

    Defined graphs will be displayed in VigiGraph.

    It is a very simple class, defining all the Graph attributes and a single
    method to add the graph to a host definition.
    """

    def __init__(self, hosts, title, dslist, template, vlabel,
                 group="General", factors=None, last_is_max=False,
                 min=None, max=None):
        """
        @param hosts: the main hosts configuration dictionary
        @type  hosts: C{dict}
        @param title: The graph title
        @type  title: C{str}
        @param dslist: The list of datasources to include
        @type  dslist: C{list} of C{str}
        @param template: The name of the graph template
        @type  template: C{str}
        @param vlabel: The vertical label
        @type  vlabel: C{str}
        @param group: The group of the graph
        @type  group: C{str}
        @param factors: the factors to use, if any
        @type  factors: C{dict}
        @param last_is_max: le dernier DS doit provoquer l'affichage d'une
            ligne horizontale noire (limite supérieure) et ne pas être listé
            dans la légende
        @type  last_is_max: C{bool}
        @param min: valeur plancher du graphe
        @type  min: C{float}
        @param max: valeur plafond du graphe
        @type  max: C{float}
        """
        self.hosts = hosts
        self.title = unicode(title)
        self.dslist = dslist
        self.template = unicode(template)
        self.vlabel = unicode(vlabel)
        self.group = unicode(group)
        if factors is None:
            self.factors = {}
        else:
            self.factors = factors
        self.last_is_max = last_is_max
        self.min = min
        self.max = max

    def add_to_host(self, hostname):
        """
        Add a graph to the host
        @param hostname: the hostname to add the graph to
        @type  hostname: C{str}
        """
        if not self.hosts[hostname].has_key("graphItems"):
            self.hosts[hostname]["graphItems"] = {}
        self.hosts[hostname]["graphItems"].update({
                self.title: {'template': self.template,
                             'vlabel': self.vlabel,
                             'ds': [ unicode(ds) for ds in self.dslist ],
                             'factors': self.factors,
                             'last_is_max': self.last_is_max,
                             'cdefs': [ cdef.to_dict() for cdef in self.dslist
                                        if isinstance(cdef, Cdef) ],
                             'min': self.min,
                             'max': self.max,
                             }
            })
        if not self.hosts[hostname].has_key("graphGroups"):
            self.hosts[hostname]["graphGroups"] = {}
        if self.group not in self.hosts[hostname]["graphGroups"]:
            self.hosts[hostname]["graphGroups"][self.group] = set()
        self.hosts[hostname]["graphGroups"][self.group].add(self.title)

