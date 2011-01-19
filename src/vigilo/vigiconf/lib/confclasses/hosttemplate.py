# -*- coding: utf-8 -*-
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

from __future__ import absolute_import

import os
import copy
import subprocess
from xml.etree import ElementTree as ET # Python 2.5

from vigilo.common.conf import settings

from . import get_text, get_attrib, parse_path
from .. import ParsingError
from ..external import topsort

from vigilo.common.gettext import translate
_ = translate(__name__)


class HostTemplate(object):
    """
    A template for hosts

    @ivar name: the template name
    @type name: C{str}
    @ivar data: the dict to return to the factory
    @type data: L{dict}
    """

    def __init__(self, name):
        self.name = name
        self.data = {
                "parent": [],
                "tests": [],
                "groups": [],
                "attributes": {},
                "weight": 1,
                "nagiosDirectives": {},
                "nagiosSrvDirs": {},
            }
        self.attr_types = {"snmpPort": int,
                           "snmpOIDsPerPDU": int,
                           "weight": int,
                          }
        self.deprecated_attr = {"community": "snmpCommunity",
                               }
        if name != "default":
            self.add_parent("default")

    def add_parent(self, p):
        """
        Add a parent for this template

        @param p: the name of the parent host template
        @type  p: C{str} or C{list} of C{str}
        """
        if not isinstance(p, list): # convert to list
            p = [p,]
        self.data["parent"].extend(p)

    def add_test(self, testname, args={}, weight=None):
        """
        Add a test to this host template
        @param testname: the test name
        @type  testname: C{str}
        @param args: the test arguments
        @type  args: C{dict}
        """
        if not self.data.has_key("tests"):
            self.data["tests"] = []
        t_dict = {"name": testname}
        if args:
            t_dict["args"] = args
        if weight is None:
            weight = 1
        t_dict["weight"] = weight
        self.data["tests"].append(t_dict)

    def add_group(self, *args):
        """
        Add a group to this host template
        @param args: the groups to add
        @type  args: C{str} or C{list} of C{str}
        """
        if not self.data.has_key("groups"):
            self.data["groups"] = []
        for group in args:
            if not parse_path(group):
                raise ParsingError(_('Invalid group name (%s)') % group)
            self.data["groups"].append(group)

    def add_weight(self, weight):
        self.data["weight"] = weight

    def add(self, prop, key, value):
        """
        A generic function to add a key/value to a property
        @param prop: the property to add to
        @type  prop: hashable
        @param key: the key to add to the property
        @type  key: hashable
        @param value: the value to add to the property
        @type  value: anything
        """
        if not self.data.has_key(prop):
            self.data[prop] = {}
        self.data[prop].update({key: value})

    def add_attribute(self, attrname, value):
        """
        Add an attribute to this host template
        @param attrname: the attribute name
        @type  attrname: hashable, usually C{str}
        @param value: the attribute value
        @type  value: anything
        """
        if attrname in self.deprecated_attr:
            import warnings
            warnings.warn(DeprecationWarning(_(
                'The "%s" attribute has been deprecated. '
                'Please use "%s" instead.'
            ) % (attrname, self.deprecated_attr[attrname])))
            attrname = self.deprecated_attr[attrname]

        if not self.data.has_key("attributes"):
            self.data["attributes"] = {}
        if attrname in self.attr_types \
                and not isinstance(value, self.attr_types[attrname]):
            value = self.attr_types[attrname](value)
        self.data["attributes"][attrname] = value

    def add_sub(self, prop, subprop, key, value):
        """
        A generic function to add a key/value to a subproperty
        @param prop: the property to add to
        @type  prop: hashable
        @param subprop: the subproperty to add to
        @type  subprop: hashable
        @param key: the key to add to the property
        @type  key: hashable
        @param value: the value to add to the property
        @type  value: anything
        """
        if not self.data.has_key(prop):
            self.data[prop] = {}
        if not self.data[prop].has_key(subprop):
            self.data[prop][subprop] = {}
        self.data[prop][subprop].update({key: value})

    def add_nagios_directive(self, name, value):
        """ Add a generic nagios directive

            @param name: the directive name
            @type  name: C{str}
            @param value: the directive value
            @type  value: C{str}
        """
        self.add("nagiosDirectives", name, value)

    def add_nagios_service_directive(self, service, name, value):
        """ Add a generic nagios directive for a service

            @param service: the service, ie 'Interface eth0'
            @type  service: C{str}
            @param name: the directive name
            @type  name: C{str}
            @param value: the directive value
            @type  value: C{str}
        """
        self.add_sub("nagiosSrvDirs", service, name, value)


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

    def __init__(self, testfactory):
        self.path = [
                      os.path.join(
                        settings["vigiconf"].get("confdir"),
                        "hosttemplates"),
                    ]
        self.testfactory = testfactory


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
                if not tplfile.endswith(".xml") or tplfile.startswith("__"):
                    continue
                self.__validate(os.path.join(pathdir, tplfile))
                self.__load(os.path.join(pathdir, tplfile))
        self.apply_inheritance()

    def __validate(self, source):
        """
        Validate the XML against the XSD using xmllint
        @param source: an XML file (or stream)
        @type  source: C{str} or C{file}
        """
        xsd = os.path.join(os.path.dirname(__file__), "..", "..",
                           "validation", "xsd", "hosttemplate.xsd")
        devnull = open("/dev/null", "w")
        result = subprocess.call(["xmllint", "--noout", "--schema", xsd, source],
                    stdout=devnull, stderr=subprocess.STDOUT)
        devnull.close()
        # Lorsque le fichier est valide.
        if result == 0:
            return
        # Plus assez de mémoire.
        if result == 9:
            raise ParsingError(_("Not enough memory to validate %(file)s "
                                 "using schema %(schema)s") % {
                                    'schame': xsd,
                                    'file': source,
                                })
        # Schéma de validation ou DTD invalide.
        if result in (2, 5):
            raise ParsingError(_("Invalid XML validation schema %(schema)s "
                                "found while validating %(file)s") % {
                                    'schema': xsd,
                                    'file': source,
                                })
        # Erreur de validation du fichier par rapport au schéma.
        if result in (3, 4):
            raise ParsingError(_("XML validation failed (%(file)s with "
                                "schema %(schema)s)") % {
                                    'schema': xsd,
                                    'file': source,
                                })
        raise ParsingError(_("XML validation failed for file %(file)s, "
                            "using schema %(schema)s, due to an error. "
                            "Make sure the permissions are set correctly.") % {
                                'schema': xsd,
                                'file': source,
                            })

    def __load(self, source):
        """
        Load a template from XML
        @param source: an XML file (or stream)
        @type  source: C{str} or C{file}
        """
        test_name = None
        cur_tpl = None
        process_nagios = False

        for event, elem in ET.iterparse(source, events=("start", "end")):
            if event == "start":
                if elem.tag == "template":
                    test_name = None

                    name = get_attrib(elem, 'name')
                    cur_tpl = HostTemplate(name)

                elif elem.tag == "test":
                    test_name = get_attrib(elem, 'name')

                    for arg in elem.getchildren():
                        if arg.tag == 'arg':
                            tname = get_attrib(arg, 'name')
                            if tname == "label":
                                test_name = "%s %s" % (test_name, get_text(arg))
                                break

                elif elem.tag == "nagios":
                    process_nagios = True


            else: # Évenement de type "end"
                if elem.tag == "parent":
                    cur_tpl.add_parent(get_text(elem))

                elif elem.tag == "class":
                    cur_tpl.classes.append(get_text(elem))

                elif elem.tag == "directive":
                    if not process_nagios: continue

                    dvalue = get_text(elem).strip()
                    dname = get_attrib(elem, 'name').strip()
                    if not dname:
                        continue

                    if test_name is None:
                        # directive host nagios
                        cur_tpl.add_nagios_directive(dname, dvalue)
                    else:
                        # directive de service nagios
                        cur_tpl.add_nagios_service_directive(test_name, dname,
                                                             dvalue)

                elif elem.tag == "attribute":
                    value = get_text(elem)
                    items = [get_text(i) for i in elem.getchildren()
                                     if i.tag == "item"]
                    if items:
                        value = items
                    cur_tpl.add_attribute(get_attrib(elem, 'name'), value)

                elif elem.tag == "group":
                    cur_tpl.add_group(get_text(elem))

                elif elem.tag == "test":
                    test_name = get_attrib(elem, 'name')
                    test_weight = get_attrib(elem, 'weight')
                    try:
                        test_weight = int(test_weight)
                    except ValueError:
                        raise ParsingError(_("Invalid weight value for test "
                            "%(test)s in template %(tpl)s: %(weight)r") % {
                            'test': test_name,
                            'tpl': cur_tpl.name,
                            'weight': test_weight,
                        })
                    except TypeError:
                        pass # C'est None, on laisse prendre la valeur par défaut
                    args = {}
                    for arg in elem.getchildren():
                        args[get_attrib(arg, 'name')] = get_text(arg)
                    cur_tpl.add_test(test_name, args, test_weight)
                    test_name = None

                elif elem.tag == "nagios":
                    process_nagios = False

                elif elem.tag == "weight":
                    weight = get_text(elem)
                    try:
                        weight = int(weight)
                    except ValueError:
                        raise ParsingError(_("Invalid weight value for "
                            "template %(tpl)s: %(weight)r") % {
                            'tpl': cur_tpl.name,
                            'weight': weight,
                        })
                    except TypeError:
                        pass # C'est None, on laisse prendre la valeur par défaut
                    cur_tpl.add_weight(weight)

                elif elem.tag == "template":
                    self.register(cur_tpl)
                    cur_tpl = None
                    elem.clear()

    def register(self, hosttemplate):
        """
        Store a hosttemplate's data in the main hashmap

        @param hosttemplate: The host template to register
        @type  hosttemplate: L{HostTemplate}
        """
        self.templates[hosttemplate.name] = hosttemplate.data

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
            if not tpl.has_key("parent") or not tpl["parent"]:
                # the "default" template is removed from self.templates,
                # all hosts will automatically add it (in Host.__init__())
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
            if not templates_save[tplname]["parent"]:
                # No parent, copy it back untouched
                self.templates[tplname] = copy.deepcopy(templates_save[tplname])
                continue
            parent = templates_save[tplname]["parent"]
            if not isinstance(parent, list): # Convert to list
                parent = [ parent, ]
            # Start by copying the first parent
            self.templates[tplname] = copy.deepcopy(self.templates[parent[0]])
            # Next, extend with the other parents (if any)
            for p in parent[1:]:
                self.templates[tplname]["groups"].extend(
                                    self.templates[p]["groups"])
                self.templates[tplname]["tests"].extend(
                                    self.templates[p]["tests"])
                self.templates[tplname]["attributes"].update(
                                    self.templates[p]["attributes"])
                self.templates[tplname]["weight"] = self.templates[p]["weight"]
                self.templates[tplname]["nagiosDirectives"].update(
                                    self.templates[p]["nagiosDirectives"])
                self.templates[tplname]["nagiosSrvDirs"].update(
                                    self.templates[p]["nagiosSrvDirs"])
            # Finally, re-add the template-specific data
            self.templates[tplname]["groups"].extend(
                            templates_save[tplname]["groups"])
            self.templates[tplname]["tests"].extend(
                            templates_save[tplname]["tests"])
            self.templates[tplname]["attributes"].update(
                            templates_save[tplname]["attributes"])
            self.templates[tplname]["weight"] = templates_save[tplname]["weight"]
            self.templates[tplname]["nagiosDirectives"].update(
                            templates_save[tplname]["nagiosDirectives"])
            self.templates[tplname]["nagiosSrvDirs"].update(
                            templates_save[tplname]["nagiosSrvDirs"])
            # Copy the parent list back too, it's not used except by unit tests
            self.templates[tplname]["parent"].extend(
                            templates_save[tplname]["parent"])

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

        # nagios generics
        if tpl.has_key("nagiosDirectives"):
            for name, value in tpl["nagiosDirectives"].iteritems():
                host.add_nagios_directive(name, value)

        if tpl.has_key("nagiosSrvDirs"):
            for srv, data in tpl["nagiosSrvDirs"].iteritems():
                for name, value in data.iteritems():
                    host.add_nagios_service_directive(srv, name, value)

        # tests
        if tpl.has_key("tests"):
            for testdict in tpl["tests"]:
                test_list = self.testfactory.get_test(testdict["name"],
                                                      host.classes)
                test_args = {}
                if testdict.has_key("args"):
                    test_args = testdict["args"]
                test_weight = None
                if "weight" in testdict and testdict["weight"] is not None \
                            and testdict["weight"] != 1:
                    test_weight = testdict["weight"]
                host.add_tests(test_list, args=test_args,
                               weight=test_weight)
        # attributes
        if tpl.has_key("attributes"):
            host.update_attributes(tpl["attributes"])
        # weight
        if "weight" in tpl and tpl["weight"] is not None and tpl["weight"] != 1:
            host.set_attribute("weight", tpl["weight"])


# vim:set expandtab tabstop=4 shiftwidth=4:
