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

import conf

class Graph(object):
    """
    This class defines the Graph configuration objects.

    Defined graphs will be displayed in VigiGraph.

    It is a very simple class, defining all the Graph attributes and a single
    method to add the graph to a host definition.
    """

    def __init__(self, title, dslist, template, vlabel,
                    group="General", factors=None):
        """
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
        """
        self.title = title
        self.dslist = dslist
        self.template = template
        self.vlabel = vlabel
        self.group = group
        if factors is None:
            self.factors = {}
        else:
            self.factors = factors

    def add_to_host(self, hostname):
        """
        Add a graph to the host
        @param hostname: the hostname to add the graph to
        @type  hostname: C{str}
        """
        if not conf.hostsConf[hostname].has_key("graphItems"):
            conf.hostsConf[hostname]["graphItems"] = {}
        conf.hostsConf[hostname]["graphItems"].update({
                        self.title: {'template': self.template,
                                     'vlabel': self.vlabel,
                                     'ds': self.dslist,
                                     'factors': self.factors,
                                     }
                        })
        if not conf.hostsConf[hostname].has_key("graphGroups"):
            conf.hostsConf[hostname]["graphGroups"] = {}
        if self.group not in conf.hostsConf[hostname]["graphGroups"]:
            conf.hostsConf[hostname]["graphGroups"][self.group] = set()
        conf.hostsConf[hostname]["graphGroups"][self.group].add(self.title)

