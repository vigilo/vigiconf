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
This module contains the classes needed to handle host templates
"""

import os

import conf
import lib.external.topsort as topsort


class HostTemplate(object):
    """
    A template for hosts

    @ivar name: the template name
    @type name: C{str}
    @ivar htf: the host template factory from the conf module
    @type htf: L{HostTemplateFactory}
    @ivar parent: the name of the parent host template
    @type parent: C{str} or C{list} of C{str}
    """

    def __init__(self, name, parent=None):
        self.htf = conf.hosttemplatefactory
        self.name = name
        self.htf.templates[self.name] = {
                "tests": [],
                "groups": [],
                "attributes": {},
            }
        self.parent = parent
        if parent:
            self.htf.templates[self.name]["parent"] = parent

    def add_test(self, testname, **args):
        """
        Add a test to this host template
        @param testname: the test name
        @type  testname: C{str}
        @param args: the test arguments
        @type  args: C{dict}
        """
        if not self.htf.templates[self.name].has_key("tests"):
            self.htf.templates[self.name]["tests"] = []
        t_dict = {"name": testname}
        if args:
            t_dict["args"] = args
        self.htf.templates[self.name]["tests"].append(t_dict)

    def add_group(self, *args):
        """
        Add a group to this host template
        @param args: the groups to add
        @type  args: C{str} or C{list} of C{str}
        """
        if not self.htf.templates[self.name].has_key("groups"):
            self.htf.templates[self.name]["groups"] = []
        for group in args:
            self.htf.templates[self.name]["groups"].append(group)

    def add_attribute(self, attrname, value):
        """
        Add an attribute to this host template
        @param attrname: the attribute name
        @type  attrname: hashable, usually C{str}
        @param value: the attribute value
        @type  value: anything
        """
        if not self.htf.templates[self.name].has_key("attributes"):
            self.htf.templates[self.name]["attributes"] = {}
        self.htf.templates[self.name]["attributes"][attrname] = value


class HostTemplateFactory(object):
    """
    Factory to list and access host templates.

    Contains mainly the list of templates, which is a dict where the keys
    are the templates names and the values are a sub-dict composed of
    3 keys: tests, groups, and attributes.

    The tests key's value is a list containing a dict describing the tests
    to apply to the host, and has the following structure::

        [
            { "name": "Test1",
              "args": { "arg1": value1, "arg2": value2 },
            },
            { "name": "Test2" },
            { "name": "Test3",
              "args": { "arg1": value1 },
            },
        ]

    The groups key's value is a list containing the groups to add to the
    host with the add_group() function.

    The attributes key's value is a dict containing the attributes to add
    to the hosts's entry in the hostsConf hashmap.
    """

    templates = {}

    def __init__(self):
        self.path = [ os.path.join(conf.dataDir, "conf.d", "hosttemplates"),
                      os.path.join(conf.confDir, "hosttemplates"),
                    ]


    def load_templates(self):
        """
        Get all the available templates and stores them in the self.templates
        class variable. Apply inheritance if necessary.
        """
        # re-declare global hosttemplatefactory. The keyword "global" does not
        # work because it is only used in files that are execfile'd, and global
        # is a parser instruction
        for pathdir in self.path:
            if not os.path.exists(pathdir):
                continue
            for tplfile in os.listdir(pathdir):
                if not tplfile.endswith(".py") or tplfile.startswith("__"):
                    continue
                execfile(os.path.join(pathdir, tplfile), globals())
        self.apply_inheritance()

    def apply_inheritance(self):
        """
        Load the templates inheritance. There are three steps:
         1. Sort the template dependencies (we can only load parents if they
            are already defined
         2. Start from scratch and load the parents in order
         3. Apply the template-specific data
        """
        # Sort the dependencies
        testdeps = []
        for tplname, tpl in self.templates.iteritems():
            if not tpl.has_key("parent"):
                continue
            if isinstance(tpl["parent"], list):
                for parent in tpl["parent"]:
                    testdeps.append( (parent, tplname) )
            else:
                testdeps.append( (tpl["parent"], tplname) )
        testdeps = topsort.topsort(testdeps)
        # Start fresh
        templates_save = self.templates.copy()
        self.templates = {}
        ## now copy back the templates to self.templates, starting with the
        ## parent if necessary
        for tplname in testdeps:
            if not templates_save[tplname].has_key("parent"):
                # No parent, copy it back untouched
                self.templates[tplname] = templates_save[tplname]
                continue
            parent = templates_save[tplname]["parent"]
            if not isinstance(parent, list): # Convert to list
                parent = [ parent, ]
            # Start by copying the first parent
            self.templates[tplname] = self.templates[parent[0]].copy()
            # Next, extend with the other parents (if any)
            for p in parent[1:]:
                self.templates[tplname]["groups"].extend(
                                    self.templates[p]["groups"])
                self.templates[tplname]["tests"].extend(
                                    self.templates[p]["tests"])
                self.templates[tplname]["attributes"].update(
                                    self.templates[p]["attributes"])
            # Finally, re-add the template-specific data
            self.templates[tplname]["groups"].extend(
                            templates_save[tplname]["groups"])
            self.templates[tplname]["tests"].extend(
                            templates_save[tplname]["tests"])
            self.templates[tplname]["attributes"].update(
                            templates_save[tplname]["attributes"])
    
    def apply(self, host, tplname):
        """
        Applies a template to a host
        @param host: the host to apply to
        @type  host: L{Server<lib.server.Server>}
        @param tplname: the name of the template to apply
        @type  tplname: C{str}
        """
        if not self.templates:
            self.load_templates()
        tpl = self.templates[tplname]
        # groups
        if tpl.has_key("groups"):
            for group in tpl["groups"]:
                host.add_group(group)
        # tests
        if tpl.has_key("tests"):
            for testdict in tpl["tests"]:
                if testdict.has_key("args") and testdict["args"]:
                    host.add_test(testdict["name"], **testdict["args"])
                else:
                    host.add_test(testdict["name"])
        # attributes
        if tpl.has_key("attributes"):
            conf.hostsConf[host.name].update(tpl["attributes"])


# vim:set expandtab tabstop=4 shiftwidth=4:
