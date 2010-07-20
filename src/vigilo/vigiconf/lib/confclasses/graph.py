################################################################################
#
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
This module contains the Graph class
"""

from __future__ import absolute_import


class Graph(object):
    """
    This class defines the Graph configuration objects.

    Defined graphs will be displayed in VigiGraph.

    It is a very simple class, defining all the Graph attributes and a single
    method to add the graph to a host definition.
    """

    def __init__(self, hosts, title, dslist, template, vlabel,
                    group="General", factors=None, max_values=None):
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
        @param max_values: the maximum values for each datasource, if any
        @type  max_values: C{dict}
        """
        self.hosts = hosts
        self.title = title
        self.dslist = dslist
        self.template = template
        self.vlabel = vlabel
        self.group = group
        
        if factors is None:
            self.factors = {}
        else:
            self.factors = factors

        if max_values is None:
            self.max_values = {}
        else:
            self.max_values = max_values

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
                                     'ds': self.dslist,
                                     'factors': self.factors,
                                     'max_values': self.max_values,
                                     }
                        })
        if not self.hosts[hostname].has_key("graphGroups"):
            self.hosts[hostname]["graphGroups"] = {}
        if self.group not in self.hosts[hostname]["graphGroups"]:
            self.hosts[hostname]["graphGroups"][self.group] = set()
        self.hosts[hostname]["graphGroups"][self.group].add(self.title)

