# -*- coding: utf-8 -*-
################################################################################
#
# Copyright (C) 2007-2014 CS-SI
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
from lxml import etree
import networkx as nx

from vigilo.common.conf import settings

from . import get_text, get_attrib, parse_path
from .. import ParsingError

from vigilo.common.gettext import translate, translate_narrow
_ = translate(__name__)
N_ = translate_narrow(__name__)


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
                "classes": [],
                "groups": [],
                "attributes": {},
                "nagiosDirectives": {
                    "host": {},
                    "services": {},
                },
                "tags": {},
                "weight": None, # Poids par défaut de l'hôte
                "default_service_weight": None, # Poids par défaut des services
                "default_service_warning_weight": None, # Poids warning par
                                                        # défaut des services
            }
        self.attr_types = {"snmpPort": int,
                           "snmpOIDsPerPDU": int,
                          }
        self.deprecated_attr = {
            "community": "snmpCommunity",
            "context": "snmpContext",
            "seclevel": "snmpSeclevel",
            "secname": "snmpSecname",
            "authproto": "snmpAuthproto",
            "authpass": "snmpAuthpass",
            "privproto": "snmpPrivproto",
            "privpass": "snmpPrivpass",
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
            p = [ p, ]
        self.data["parent"].extend(p)

    def add_test(self, testname, args=None, weight=None, warning_weight=None,
                 directives=None):
        """
        Add a test to this host template
        @param testname: the test name
        @type  testname: C{str}
        @param args: the test arguments
        @type  args: C{dict}
        @param directives: associated Nagios directives
        @type  directives: C{dict}
        """
        if args is None:
            args = {}
        if directives is None:
            directives = {}
        if not self.data.has_key("tests"):
            self.data["tests"] = []
        t_dict = {"name": testname}
        if args:
            t_dict["args"] = args
        t_dict["weight"] = weight
        t_dict["warning_weight"] = warning_weight
        t_dict["directives"] = directives
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

    def add_class(self, classname):
        """
        Add a class name to this host template
        @param classname: the class name to add
        @type  classname: C{str}
        """
        if not self.data.has_key("classes"):
            self.data["classes"] = []
        self.data["classes"].append(classname)

    def add_weight(self, type, weight):
        """
        Ajoute un poids à l'hôte.

        @param type: type de poids, fait partie de ["weight",
                     "default_service_weight",
                     "default_service_warning_weight"]
        @type type: C{str}
        @param weight: nouveau poids pour le type donné.
        @type weight: C{int}
        """
        self.data[type] = weight

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
            warnings.warn(DeprecationWarning(N_(
                'The "%(old_attribute)s" attribute has been deprecated. '
                'Please use "%(replacement)s" instead.'
            ) % {
                'old_attribute': attrname,
                'replacement': self.deprecated_attr[attrname],
            }))
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

    def add_tag(self, service, name, value):
        """
        Add a tag to a host or a service. This tag is associated with a value.
        @param service: the service to add the tag to. If it is the string
            "Host", then the tag is added to the host itself.
        @type  service: C{str}
        @param name: the tag name
        @type  name: C{str}
        @param value: the tag value
        @type  value: C{str}
        """
        if not service or service.lower() == "host":
            target = None
        else:
            target = service
        self.add_sub("tags", target, name, value)

    def add_nagios_directive(self, name, value, target="host"):
        """ Add a generic nagios directive

            @param name: the directive name
            @type  name: C{str}
            @param value: the directive value
            @type  value: C{str}
            @param target: the directive target (ie: where does it apply)
            @type target: C{str}
        """
        if target is None:
            target = "host"
        self.add_sub("nagiosDirectives", target, name, value)



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
    templates_deps = nx.DiGraph()

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
        xsd = self._get_xsd()
        for pathdir in self.path:
            if not os.path.exists(pathdir):
                continue
            for root, dirs, files in os.walk(pathdir):
                for f in files:
                    if not f.endswith(".xml") or f.startswith("__"):
                        continue
                    tplfile = os.path.join(root, f)
                    self._validate(tplfile, xsd)
                    self._load(tplfile)
        self._resolve_dependencies()

    def _resolve_dependencies(self):
        self.templates_deps.clear()
        for (tpl_name, tpl_data) in self.templates.iteritems():
            self.templates_deps.add_node(tpl_name)
            for parent in tpl_data['parent']:
                self.templates_deps.add_edge(tpl_name, parent)
        if not nx.is_directed_acyclic_graph(self.templates_deps):
            raise ParsingError(_("A cycle has been detected in templates"))

    def _get_xsd(self): # pylint: disable-msg=R0201
        xsd_path = os.path.join(os.path.dirname(__file__), "..", "..",
                           "validation", "xsd", "hosttemplate.xsd")
        try:
            xsd_doc = etree.parse(xsd_path)
            xsd = etree.XMLSchema(xsd_doc)
        except (etree.XMLSyntaxError, etree.XMLSchemaParseError), e:
            raise ParsingError(_("Invalid XML validation schema %(schema)s: "
                                "%(error)s") % {
                                    'schema': xsd_path,
                                    'error': str(e),
                                })
        except IOError, e:
            raise ParsingError(_("Error reading %(file)s, make sure the "
                                 "permissions are set correctly."
                                 "Message: %(error)s.") % {
                                    'file': xsd_path,
                                    'error': str(e),
                                })
        return xsd

    def _validate(self, source, xsd): # pylint: disable-msg=R0201
        """
        Validate the XML against the XSD using lxml
        @param source: an XML file (or stream)
        @type  source: C{str} or C{file}
        """
        try:
            source_doc = etree.parse(source)
        except etree.XMLSyntaxError, e:
            raise ParsingError(_("XML syntax error in %(file)s: %(error)s") %
                               { 'file': source, 'error': str(e) })
        except IOError, e:
            raise ParsingError(_("Error reading %(file)s, make sure the "
                                 "permissions are set correctly."
                                 "Message: %(error)s.") % {
                                    'file': source,
                                    'error': str(e),
                                })
        valid = xsd.validate(source_doc)
        if not valid:
            raise ParsingError(_("XML validation failed: %(error)s") % {
                                    'error': xsd.error_log.last_error,
                                })
        return source_doc

    def _load(self, source):
        """
        Load a template from XML
        @param source: an XML file (or stream)
        @type  source: C{str} or C{file}
        @todo: mettre en commun avec le parsing dans host.py
        """
        test_name = None
        cur_tpl = None
        test_directives = {}
        process_nagios = False
        weight = {
                "weight": None,
                "default_service_weight": None,
                "default_service_warning_weight": None
                }

        for event, elem in etree.iterparse(source, events=("start", "end")):
            if event == "start":
                if elem.tag == "template":
                    test_name = None

                    name = get_attrib(elem, 'name')
                    cur_tpl = HostTemplate(name)
                    weight = {
                            "weight": None,
                            "default_service_weight": None,
                            "default_service_warning_weight": None
                            }

                elif elem.tag == "nagios":
                    process_nagios = True

                elif elem.tag == "test":
                    test_name = get_attrib(elem, "name")
                    test_directives = {}

            else: # Évenement de type "end"
                if elem.tag == "force-passive":
                    cur_tpl.add_attribute("force-passive", True)

                if elem.tag == "parent":
                    cur_tpl.add_parent(get_text(elem))

                elif elem.tag == "class":
                    cur_tpl.add_class(get_text(elem))

                elif elem.tag == "directive":
                    if not process_nagios:
                        continue

                    dname = get_attrib(elem, 'name')
                    if not dname:
                        continue

                    dtarget = get_attrib(elem, 'target')
                    dvalue = get_text(elem)

                    # directive nagios générique pour un hôte ou sur
                    # l'ensemble des services (suivant la target)
                    if test_name is None:
                        cur_tpl.add_nagios_directive(dname, dvalue, target=dtarget)
                        continue

                    # directive nagios spécifique à un service
                    test_directives[dname] = dvalue

                elif elem.tag == "tag":
                    service = None
                    if 'service' in elem.attrib:
                        service = get_attrib(elem, 'service')
                    cur_tpl.add_tag(service, get_attrib(elem, 'name'), get_text(elem))

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
                    test_weight = { "weight": None,
                                    "warning_weight": None }
                    for k in test_weight.keys():
                        v = get_attrib(elem, k)
                        try:
                            test_weight[k] = int(v)
                        except ValueError:
                            raise ParsingError(
                                    _("Invalid value for %(type)s in test "
                                    "%(test)s in template %(tpl)s: %(value)r") %
                                        {'type': k,
                                         'test': test_name,
                                         'tpl': cur_tpl.name,
                                         'value': v,
                                         })
                        except TypeError:
                            # C'est None, on laisse prendre la valeur par défaut
                            pass

                    args = {}
                    for arg in elem.getchildren():
                        if arg.tag != "arg":
                            continue

                        arg_name = get_attrib(arg, 'name')
                        args[arg_name] = []
                        for item in arg.getchildren():
                            if item.tag == 'item':
                                args[arg_name].append(get_text(item))

                        # S'il y avait effectivement une liste de valeurs,
                        # on la transforme en tuple pour éviter toute
                        # modification dans les tests.
                        if args[arg_name]:
                            args[arg_name] = tuple(args[arg_name])
                        # Sinon, l'argument n'a qu'une seule valeur,
                        # qu'on récupère ici.
                        else:
                            args[arg_name] = get_text(arg)
                    cur_tpl.add_test(test_name, args, test_weight["weight"],
                                     test_weight["warning_weight"],
                                     test_directives)
                    test_name = None

                elif elem.tag in weight:
                    value = get_text(elem)
                    try:
                        weight[elem.tag] = int(value)
                    except ValueError:
                        raise ParsingError(_("Invalid value for %(type)s in "
                            "template %(tpl)s: %(value)r") % {
                            'type': elem.tag,
                            'tpl': cur_tpl.name,
                            'value': value,
                        })
                    except TypeError:
                        # C'est None, on laisse prendre la valeur par défaut
                        pass

                    cur_tpl.add_weight(elem.tag, weight[elem.tag])

                elif elem.tag == "nagios":
                    process_nagios = False

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

    def apply(self, host, tplname):
        """
        Applies a template to a host
        @param host: the host to apply to
        @type  host: L{Host<vigilo.vigiconf.lib.confclasses.host.Host>}
        @param tplname: the name of the template to apply
        @type  tplname: C{str}
        """
        if not self.templates:
            self.load_templates()
        try:
            tpl = self.templates[tplname]
        except (KeyError, ValueError):
            raise ParsingError(_('Can\'t add template "%(template)s" to host '
                                 '"%(hostname)s": no such template') % {
                                    "template": tplname,
                                    "hostname": host.name,
                                })


        # force-passive
        if tpl.has_key("force-passive"):
            host.set_attribute("force-passive", True)

        # groups
        if tpl.has_key("groups"):
            for group in tpl["groups"]:
                host.add_group(group)

        # nagios generics
        for target in tpl["nagiosDirectives"]:
            for name, value in tpl["nagiosDirectives"][target].iteritems():
                host.add_nagios_directive(name, value, target=target)

        # class
        if tpl.has_key("classes"):
            for class_ in tpl["classes"]:
                host.add_class(class_)

        # attributes
        if tpl.has_key("attributes"):
            host.update_attributes(tpl["attributes"])

        # tests
        if tpl.has_key("tests"):
            for testdict in tpl["tests"]:
                test_list = self.testfactory.get_test(testdict["name"],
                                                      host.classes)
                if not test_list:
                    raise ParsingError(_("Can't add test %(testname)s to host "
                            "%(hostname)s (added by template %(tplname)s). "
                            "Maybe a missing host class ?")
                            % {"tplname": tplname,
                               "hostname": host.name,
                               "testname": testdict["name"]})

                test_args = testdict.get("args", {})
                test_weight = testdict.get("weight")
                test_warn_weight = testdict.get("warning_weight")

                host.add_tests(test_list, args=test_args, weight=test_weight,
                               warning_weight=test_warn_weight,
                               directives=testdict["directives"])

        # tags
        if tpl.has_key("tags"):
            for target in tpl['tags']:
                for name, value in tpl['tags'][target].iteritems():
                    host.add_tag(target, name, value)

        # Poids
        host_weight = [ "weight",
                        "default_service_weight",
                        "default_service_warning_weight" ]
        for k in host_weight:
            if tpl.get(k) is not None:
                host.set_attribute(k, tpl[k])

# vim:set expandtab tabstop=4 shiftwidth=4:
