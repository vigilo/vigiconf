# -*- coding: utf-8 -*-
# Copyright (C) 2007-2020 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
This module contains the Host class
"""

from __future__ import absolute_import

import os
import inspect
from lxml import etree
from vigilo.common.nx import networkx as nx

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate, translate_narrow
_ = translate(__name__)
N_ = translate_narrow(__name__)

from . import get_text, get_attrib
from .graph import Graph, Cdef
from vigilo.common import parse_path
from vigilo.vigiconf.lib import ParsingError, VigiConfError
from vigilo.vigiconf.lib import SNMP_ENTERPRISE_OID


class Host(object):
    """
    The Host configuration class.

    This class defines all the attributes and the methods of hosts in the
    configuration system.

    The attributes are added to the hosts hashmap, and the methods
    directly modify this hashmap.

    The methods are used by the tests definitions.

    @ivar hosts: the main hosts configuration dictionary
    @type hosts: C{dict}
    @ivar name: the hostname
    @type name: C{str}
    """
    def __init__(self, hosts, filename, name, address, servergroup):
        self.hosts = hosts
        self.name = name

        if self.name in self.hosts:
            raise VigiConfError(_("Host '%(host)s' defined in multiple "
                                  "files (%(file1)s and %(file2)s)") %
                                {
                                    'host': self.name,
                                    'file1': self.hosts[name]['filename'],
                                    'file2': filename,
                                })

        self.hosts[name] = {
                "filename": unicode(filename),
                "name": name,
                "address": address,
                "serverGroup": servergroup,
                "otherGroups": set(),
                "services"       : {},
                "dataSources"    : {},
                "PDHandlers"     : {},
                "SNMPJobs"       : {},
                "telnetJobs"     : {},
                "metro_services" : {},
                "graphItems"     : {},
                "routeItems"     : {},
                "snmpTrap"       : {},
                "netflow"        : {},
                "graphGroups"    : {},
                "reports"        : {},
                "snmpTransport"  : u"udp",
                "snmpVersion"    : u"2",
                "snmpCommunity"  : u"public",
                "snmpPort"       : 161,
                "snmpOIDsPerPDU" : 10,
                "collectorTimeout": 3,
                "nagiosDirectives": {
                    "host": {
                        "check_command": "check-host-alive",
                        "use": "generic-active-host",
                    },
                    "services": {},
                },
                "nagiosSrvDirs"  : {},
                "force-passive"  : False,
            }
        self.attr_types = {"snmpPort": int,
                           "snmpOIDsPerPDU": int,
                           "collectorTimeout": int,
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

    def get_attribute(self, attribute, default=False):
        """
        A very simple wrapper to get an attribute from the
        host's entry in the hashmap.
        @param attribute: the attribute to get
        @param default: default value if the attribute is not found
        """
        if self.hosts[self.name].has_key(attribute):
            return self.hosts[self.name][attribute]
        else:
            return default

    def set_attribute(self, attribute, value):
        """
        A very simple wrapper to set an attribute in the
        host's entry in the hashmap.
        @param attribute: the attribute to set
        @param value: the value to set the attribute to
        """
        if attribute in self.deprecated_attr:
            import warnings
            warnings.warn(DeprecationWarning(N_(
                'The "%(old_attribute)s" attribute has been deprecated. '
                'Please use "%(replacement)s" instead.'
            ) % {
                'old_attribute': attribute,
                'replacement': self.deprecated_attr[attribute],
            }))
            attribute = self.deprecated_attr[attribute]
        if attribute in self.attr_types \
                and not isinstance(value, self.attr_types[attribute]):
            value = self.attr_types[attribute](value)
        if (attribute in self.hosts[self.name]
                and type(value) != type(self.hosts[self.name][attribute])):
            # On vient d'essayer d'ajouter un attribut sur une valeur réservée
            # comme dataSources ou services
            raise ParsingError(_("In host %(host)s: attribute name "
                                 "%(attribute)s is reserved")
                                 % {"host": self.name, "attribute": attribute})
        self.hosts[self.name][attribute] = value

    def update_attributes(self, attributes):
        """
        A very simple wrapper to set many attributes at once in the host's
        entry in the hashmap.
        This is used by the hosttemplate factory to apply attributes from
        a host template.

        @param attributes: the attributes to set
        @type  attributes: C{dict}
        """
        for attr_name, attr_value in attributes.iteritems():
            self.set_attribute(attr_name, attr_value)

    def add_tests(self, test_class, args=None, directives=None):
        """
        Add a list of tests to this host, with the provided arguments

        @param test_class: a test class to add
        @type  test_class: C{Test<.test.Test>}
        @param args: the test arguments
        @type  args: C{dict}
        @param directives: A dictionary of directives to be passed on
            to Nagios.
        @type  directives: C{dict}
        """
        if directives is None:
            directives = {}
        if args is None:
            args = {}

        inst = test_class(self, directives)
        try:
            inst.add_test(**args)
        except TypeError:
            test = getattr(inst.add_test, 'wrapped_func', inst.add_test)
            spec = inspect.getargspec(test)
            # On récupère la liste des arguments obligatoires,
            # en prenant soin de supprimer l'argument "self".
            defaults = spec[3]
            if defaults is None:
                args = spec[0][1:]
            else:
                args = spec[0][1:-len(defaults)]
            hclass = test_class.__module__.rsplit('.', 2)[-2]
            message = _('Test "%(class)s.%(test)s" on "%(host)s" needs the '
                        'following arguments: %(args)s') \
                      % {'class': hclass,
                         'test': str(test_class.__name__),
                         'host': self.name,
                         'args': ', '.join(args),
                        }
            raise VigiConfError(message)


#### Access the global dicts ####

    def add_group(self, group_name):
        """
        Add the host to a new secondary group
        @param group_name: the group to be added to
        @type  group_name: C{str}
        """
        group_name = unicode(group_name)
        self.hosts[self.name]['otherGroups'].add(group_name)

#### Access the hosts dict ####

    def get(self, prop):
        """
        A generic function to get a property from the main hashmap
        @param prop: the property to get
        @type  prop: hashable
        """
        return self.hosts[self.name][prop]

    def add(self, hostname, prop, key, value):
        """
        A generic function to add a key/value to a property
        @param hostname: the hostname to add to. Usually L{name}.
        @type  hostname: C{str}
        @param prop: the property to add to
        @type  prop: hashable
        @param key: the key to add to the property
        @type  key: hashable
        @param value: the value to add to the property
        @type  value: anything
        """
        if not self.hosts[hostname].has_key(prop):
            self.hosts[hostname][prop] = {}
        self.hosts[hostname][prop].update({key: value})

    def add_sub(self, hostname, prop, subprop, key, value):
        """
        A generic function to add a key/value to a subproperty
        @param hostname: the hostname to add to. Usually L{name}.
        @type  hostname: C{str}
        @param prop: the property to add to
        @type  prop: hashable
        @param subprop: the subproperty to add to
        @type  subprop: hashable
        @param key: the key to add to the property
        @type  key: hashable
        @param value: the value to add to the property
        @type  value: anything
        """
        if not self.hosts[hostname].has_key(prop):
            self.hosts[hostname][prop] = {}
        if not self.hosts[hostname][prop].has_key(subprop):
            self.hosts[hostname][prop][subprop] = {}
        self.hosts[hostname][prop][subprop].update({key: value})

    def add_trap(self, oid, state, service=None, message=None, conditions=None,
                 directives=None):
        """
        Add a trap handler.
        @param oid: Trap to handle
        @type oid: C{str}
        @param state: State to use for this trap
        @type state: C{str}
        @param service: Service to update in Nagios
        @type service: C{str}
        @param message: Message associated with the trap
        @type message: C{str}
        @param conditions: Conditions for the trap
        @type conditions: C{list}
        @param directives: A dictionary of directives to be passed on
            to Nagios.
        @type  directives: C{dict}
        """
        if conditions is None:
            conditions = []

        if directives is None:
            directives = {}

        if service and service not in self.hosts[self.name]["services"]:
            self.add_custom_service(service, "passive")

        target = "nagiosSrvDirs" if service else "nagiosDirectives"
        for (name, value) in directives.iteritems():
            self.add_sub(self.name, target, service or "host", name, str(value))
        self.add_sub(self.name, target, service or "host",
                     "passive_checks_enabled", "1")

        self.hosts[self.name]["snmpTrap"].setdefault(service, []).append(
            (oid, state, message, conditions)
        )

    def add_netflow(self, data=None):
        """
        Add netflow handler (for pmacct and pmacct-snmp)
        @param data: dictionary contains data like inbound, outbound, binary
        path and IP list.
        @type data: C{dict}
        """
        if data is None:
            data = {}
        if not self.hosts[self.name].has_key("netflow"):
            self.hosts[self.name]["netflow"] = {}
        self.hosts[self.name]["netflow"] = data.copy()

#### Collector-related functions ####

    def add_collector_service(self, label, function, params, variables,
                              reroutefor=None, directives=None):
        """
        Add a supervision service to the Collector
        @param label: the service display label
        @type  label: C{str}
        @param function: the Collector function to use
        @type  function: C{str}
        @param params: the parameters for the Collector function
        @type  params: C{list}
        @param variables: the variables for the Collector function
        @type  variables: C{list}
        @param reroutefor: Service routing information.
            This parameter indicates that the given service receives
            information for another service, whose host and label are
            given by the "host" and "service" keys of this dict,
            respectively.
        @type  reroutefor: C{dict}
        @param directives: A dictionary of directives to be passed on
            to Nagios.
        @type  directives: C{dict}
        """
        # Si il n'existe pas encore, on ajoute un test Collector par défaut
        # pour être sûr que les données soient collectées.
        if "Collector" not in self.hosts[self.name]["services"]:
            self.add_external_sup_service("Collector", "Collector",
                    directives={"max_check_attempts": "2"})
        # Handle rerouting
        if reroutefor == None:
            target = self.name
            service = label
            reroutedby = None
        else:
            target = reroutefor["host"]
            service = reroutefor['service']
            reroutedby = {'host': self.name, 'service': label, }

        if directives is None:
            directives = {}
        for (dname, dvalue) in directives.iteritems():
            self.add_sub(target, "nagiosSrvDirs", service, dname, str(dvalue))

        # Add the Nagios service (rerouting-dependant)
        # On utilise add_sub() car sinon on risque d'écraser complètement
        # une configuration déjà en place, par exemple lorsque des tags
        # ont été définis pour ce service.
        definition = {
            'type': 'passive',
            'directives': directives,
            'reRoutedBy': reroutedby,
        }
        for (key, value) in definition.iteritems():
            self.add_sub(target, "services", service, key, value)

        # Add the Collector service (rerouting is handled inside the Collector)
        self.add(self.name, "SNMPJobs", (label, 'service'),
                                        {'function': function,
                                         'params': params,
                                         'vars': variables,
                                         'reRouteFor': reroutefor,
                                         } )

    def add_collector_metro(self, name, function, params, variables, dstype,
                            label=None, reroutefor=None, max_value=None,
                            min_value=None, rra_template=None):
        """
        Add a metrology datasource to the Collector
        @param name: the datasource name
        @type  name: C{str}
        @param function: the Collector function to use
        @type  function: C{str}
        @param params: the parameters for the Collector function
        @type  params: C{list}
        @param variables: the variables for the Collector function
        @type  variables: C{list}
        @param dstype: datasource type
        @type  dstype: "GAUGE" or "COUNTER", see RRDtool documentation
        @param label: the datasource display label
        @type  label: C{str}
        @param reroutefor: service routing information
        @type  reroutefor: C{dict} with "host" and "service" as keys
        @param max_value: the maximum values for the datasource, if any
        @type  max_value: C{int}
        @param rra_template: RRA template to use. It omitted, generators
            use a default template.
        @type  rra_template: C{str}
        """
        if "Collector" not in self.hosts[self.name]["services"]:
            self.add_external_sup_service("Collector", "Collector",
                    directives={"max_check_attempts": "2"})
        if not label:
            label = name
        # Handle rerouting
        if reroutefor is None:
            target = self.name
            service = name
        else:
            target = reroutefor['host']
            service = reroutefor['service']

        # Add the RRD datasource (rerouting-dependant)
        self.add(target, "dataSources", service, {
            'dsType': dstype,
            'label': label,
            "max": max_value,
            "min": min_value,
            "rra_template": rra_template,
        })
        # Add the Collector service (rerouting is handled inside the Collector)
        self.add(self.name, "SNMPJobs", (name, 'perfData'),
                                        {'function': function,
                                         'params': params,
                                         'vars': variables,
                                         'reRouteFor': reroutefor,
                                         } )

    def add_graph(self, title, dslist, template, vlabel, group="General",
                  factors=None, last_is_max=False, min=None, max=None):
        """
        Add a graph to the host
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
        for ds in dslist:
            if isinstance(ds, Cdef):
                ds = ds.name
            if ds not in self.hosts[self.name]["dataSources"]:
                raise VigiConfError(_("host '%(host)s': wrong datasource in "
                    "graph '%(graph)s': %(ds)s")
                    % {"graph": title, "ds": ds, "host": self.name})
        graph = Graph(self.hosts, title, dslist, template, vlabel,
                      group=group, factors=factors, last_is_max=last_is_max,
                      min=min, max=max)
        graph.add_to_host(self.name)

    def make_rrd_cdef(self, name, cdef, rra_template=None):
        self.add(self.name, "dataSources", name, {
            'dsType': "CDEF",
            'name': name,
            'label': name,
            "max": None,
            "min": None,
            "rra_template": rra_template,
        })
        try:
            return Cdef(name, cdef)
        except (UnicodeEncodeError, UnicodeDecodeError) as e:
            try:
                errmsg = unicode(e)
            except UnicodeDecodeError:
                errmsg = unicode(str(e), 'utf-8', 'replace')
            raise VigiConfError(_("CDEF name must be ASCII-only: %s")
                                % errmsg)

    def add_external_sup_service(self, name, command=None, directives=None):
        """
        Add a standard Nagios service
        @param name: the service name
        @type  name: C{str}
        @param command: the command to use
        @type  command: C{str}
        @param directives: A dictionary of directives to be passed on
            to Nagios.
        @type  directives: C{dict}
        """
        if directives is None:
            directives = {}
        for (dname, dvalue) in directives.iteritems():
            self.add_sub(self.name, "nagiosSrvDirs", name, dname, dvalue)

        definition =  {'command': command,
                       'directives': directives,
                       'reRoutedBy': None,
                      }
        if command is None:
            definition["type"] = "passive"
        else:
            if self.get_attribute("force-passive"):
                definition["type"] = "passive"
            else:
                definition["type"] = "active"
            definition["command"] = command
        for (key, value) in definition.iteritems():
            self.add_sub(self.name, 'services', name, key, value)

    def add_custom_service(self, name, stype, directives=None):
        """
        Ajoute un service Nagios quasiment entièrement défini par un des
        modèles fournis dans le générateur Nagios.
        Exemples: metro, connector.
        @param name: the service name
        @type  name: C{str}
        @param stype: the service type
        @type  stype: C{str}
        @param directives: A dictionary of directives to be passed on
            to Nagios.
        @type  directives: C{dict}
        """
        if directives is None:
            directives = {}
        for (dname, dvalue) in directives.iteritems():
            self.add_sub(self.name, "nagiosSrvDirs", name, dname, dvalue)

        definition =  {'type': stype,
                       'directives': directives,
                       'reRoutedBy': None,
                      }
        if self.get_attribute("force-passive"):
            definition["type"] = "passive"
        for (key, value) in definition.iteritems():
            self.add_sub(self.name, 'services', name, key, value)

    def add_perfdata(self, name, label, dstype="GAUGE", reroutefor=None,
            max_value=None, min_value=None, rra_template=None):
        """
        Add a perfdata: associate a RRD file to a host.
        @param name: the datasource name (rrd filename)
        @type  name: C{str}
        @param label: the datasource display label
        @type  label: C{str}
        @param dstype: datasource type
        @type  dstype: "GAUGE" or "COUNTER", see RRDtool documentation
        @param reroutefor: service routing information
        @type  reroutefor: C{dict} with "host" and "service" as keys
        @param max_value: the maximum value for the datasource, if any
        @type  max_value: C{int}
        @param min_value: the minimal value for the datasource, if any
        @type  min_value: C{int}
        @param rra_template: RRA template to use. It omitted, generators
            use a default template.
        @type  rra_template: C{str}
        """
        if reroutefor is None:
            target = self.name
        else:
            target = reroutefor['host']
        # Add the RRD
        self.add(target, "dataSources", name,
                 {'dsType': dstype, 'label': label,
                  "max": max_value, "min": min_value,
                  "rra_template": rra_template})

    def add_perfdata_handler(self, service, name, label, perfdatavarname,
            dstype="GAUGE", reroutefor=None, max_value=None,
            min_value=None, rra_template=None):
        """
        Add a perfdata handler: send the performance data from the nagios
        plugins to the RRDs
        @param service: the service name
        @type  service: C{str}
        @param name: the datasource name (rrd filename)
        @type  name: C{str}
        @param label: the datasource display label
        @type  label: C{str}
        @param perfdatavarname: the name of the perfdata indicator
        @type  perfdatavarname: C{str}
        @param dstype: datasource type
        @type  dstype: "GAUGE" or "COUNTER", see RRDtool documentation
        @param reroutefor: service routing information
        @type  reroutefor: C{dict} with "host" and "service" as keys
        @param max_value: the maximum value for the datasource, if any
        @type  max_value: C{int}
        @param min_value: the minimal value for the datasource, if any
        @type  min_value: C{int}
        @param rra_template: RRA template to use. It omitted, generators
            use a default template.
        @type  rra_template: C{str}
        """
        # Add the RRD
        self.add_perfdata(name, label, dstype=dstype, reroutefor=reroutefor,
                max_value=max_value, min_value=min_value,
                rra_template=rra_template)
        # Add the perfdata handler in Nagios
        if not self.get('PDHandlers').has_key(service):
            self.add(self.name, "PDHandlers", service, [])
        existing = [ pdh["perfDataVarName"] for pdh in
                     self.hosts[self.name]['PDHandlers'][service] ]
        if perfdatavarname not in existing:
            self.hosts[self.name]['PDHandlers'][service].append(
                    {'name': name, 'perfDataVarName': perfdatavarname,
                     'reRouteFor': reroutefor})

    def add_metro_service(self, servicename, metroname, warn, crit,
                          factor=1, directives=None):
        """
        Add a Nagios test on the values stored in a RRD file
        @param servicename: the name of the Nagios service
        @type  servicename: C{str}
        @param metroname: the name of the metrology datasource
        @type  metroname: C{str}
        @param warn: the WARNING threshold.
        @type  warn: C{str}
        @param crit: the CRITICAL threshold.
        @type  crit: C{str}
        @param factor: the factor to use, if any
        @type  factor: C{int} or C{float}
        @param directives: A dictionary of directives to be passed on
            to Nagios.
        @type  directives: C{dict}
        """
        # Ajout du service Nagios
        self.add_custom_service(servicename, "passive", directives=directives)
        # Ajout des seuils pour le connector-metro.
        self.add(self.name, "metro_services", metroname, {
            'servicename': servicename,
            'warning': warn,
            'critical': crit,
            'factor': factor,
        })

    def add_telnet_service(self, servicename, params, directives=None):
        """
        Ajoute un service pour collecte via le collector-telnet.

        @param servicename: Nom du service qui sera ajouté au collector-telnet.
        @type  servicename: C{str}
        @param params: Dictionnaire de paramètres pour réaliser la collecte
            de ce service.
        @type  params: C{dict}
        @param directives: A dictionary of directives to be passed on
            to Nagios.
        @type  directives: C{dict}
        """
        # Précaution contre les écrasements.
        if servicename == "General":
            raise VigiConfError(_("Cannot override general configuration."))
        # Ajout de la configuration générale du collector-telnet.
        if "General" not in self.hosts[self.name].get("telnetJobs"):
            telnetLogin = self.get_attribute("telnetLogin", None)
            telnetPassword = self.get_attribute("telnetPassword", None)
            timeout = self.get_attribute("timeout", 10)
            prompt_timeout = self.get_attribute("prompt_timeout", 5)

            if telnetLogin is None or telnetPassword is None:
                raise VigiConfError(
                    _("telnetLogin and telnetPassword cannot be empty")
                )

            error_msg = _("Value for '%(attr)s' (%(value)s) could not be cast "
                          "into an integer. Using default value (%(default)d).")
            try:
                timeout = int(timeout)
            except ValueError:
                default = 10
                LOGGER.info(error_msg, {
                                'value': timeout,
                                'default': default,
                                'attr': 'timeout',
                            })
                timeout = default

            try:
                prompt_timeout = int(prompt_timeout)
            except ValueError:
                default = 5
                LOGGER.info(error_msg, {
                                'value': prompt_timeout,
                                'default': default,
                                'attr': 'prompt_timeout',
                            })
                prompt_timeout = default

            self.add(self.name, "telnetJobs", "General", {
                "login": telnetLogin,
                "pass": telnetPassword,
                "timeout": timeout,
                "prompt_timeout": prompt_timeout,
            })

        # Ajout du plugin dans le collector-telnet.
        self.add(self.name, "telnetJobs", servicename, params)
        # Ajout d'un service passif pour le plugin.
        self.add_custom_service(servicename, "passive", directives=directives)
        # Ajout du collector-telnet lui-même dans les services.
        if "Collector Telnet" not in self.hosts[self.name].get("services"):
            self.add_external_sup_service("Collector Telnet",
                        "collector_telnet!%s.py" % self.name)

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
            target = self.hosts[self.name]
        else:
            if not self.hosts[self.name]["services"].has_key(service):
                raise ParsingError(_('Cannot add tag "%(tag)s" to non-existing '
                                     'service "%(service)s"') % {
                                        'tag': name,
                                        'service': service,
                                    })
            target = self.hosts[self.name]["services"][service]
        if not target.has_key("tags"):
            target["tags"] = {}
        target["tags"][name] = value

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
        if value is None:
            raise ParsingError(_('Empty value given for directive '
                                 '%(directive)s with target %(target)s '
                                 'on host %(host)s') % {
                                    'directive': name,
                                    'target': target,
                                    'host': self.name,
                                })
        self.add_sub(self.name, "nagiosDirectives", target, name, str(value))



class HostFactory(object):
    """
    Factory to create Host objects
    """

    def __init__(self, hostsdir, hosttemplatefactory, testfactory):
        self.hosts = {}
        self.hosttemplatefactory = hosttemplatefactory
        self.testfactory = testfactory
        self.hostsdir = hostsdir

# VIGILO_EXIG_VIGILO_CONFIGURATION_0010 : Fonctions de préparation des
#   configurations de la supervision en mode CLI
#
#   configuration des hôtes à superviser : ajout/modification/suppression
#     d'un hôte ou d'une liste d'hôtes
#   configuration des paramètres d'authentification SNMP pour chaque hôte à
#     superviser ( version V1,V2c,V3) et adresse IP pour l'interface SNMP
#   configuration des services et seuils d'alarmes :
#     ajout/modification/suppression d'un service et positionnement des seuils
#     d'alarme Warning/Critical/OK
#   configuration des valeurs de performances à collecter :
#     ajout/modification/suppression d'une valeur de performance
#   configuration des cartes automatiques;
    def load(self, validation=True):
        """
        Load the defined hosts
        """
        # préparation de la validation
        if validation:
            xsd = self._get_xsd()
        # parcours des répertoires
        for root, dirs, files in os.walk(self.hostsdir):
            for f in files:
                if not f.endswith(".xml"):
                    continue
                hostfile = os.path.join(root, f)
                if validation:
                    hostxml = self._validatehost(hostfile, xsd)
                else:
                    hostxml = None
                self._loadhosts(hostfile, hostxml)
                LOGGER.debug("Successfully parsed %s", hostfile)
            for d in dirs: # Don't visit subversion/CVS directories
                if d.startswith("."):
                    dirs.remove(d)
                if d == "CVS":
                    dirs.remove("CVS")
        return self.hosts

    def _get_xsd(self): # pylint: disable-msg=R0201
        xsd_path = os.path.join(os.path.dirname(__file__), "..", "..",
                           "validation", "xsd", "host.xsd")
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

    def _validatehost(self, source, xsd): # pylint: disable-msg=R0201
        """
        Validate the XML against the XSD using lxml
        @param source: an XML file (or stream)
        @type  source: C{str} or C{file}
        """
        try:
            source_doc = etree.parse(source)
        except etree.XMLSyntaxError as e:
            raise ParsingError(_("XML syntax error in %(file)s: %(error)s") %
                               { 'file': source, 'error': str(e) })
        except IOError as e:
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

    def _loadhosts(self, source, sourcexml=None):
        """
        Load a Host from an XML file

        TODO: refactoring: implémenter un loader XML pour les hosts, comme pour
        les autres entités.

        @param source: an XML file (or stream)
        @type  source: C{str} or C{file}
        @todo: mettre en commun avec le parsing dans hosttemplate.py
        """
        test_name = None
        cur_host = None
        process_nagios = False
        test_directives = {}
        directives = {}
        tests = []
        templates = []

        if sourcexml is not None:
            iterator = etree.iterwalk
            xml = sourcexml
        else:
            iterator = etree.iterparse
            xml = source
        for event, elem in iterator(xml, events=("start", "end")):
            if event == "start":
                if elem.tag == "host":
                    test_name = None
                    directives = {}
                    tests = []
                    tags = []
                    templates = []
                    attributes = {}

                    name = get_attrib(elem, 'name')

                    address = get_attrib(elem, 'address')
                    if not address:
                        address = name

                    ventilation = get_attrib(elem, 'ventilation')

                    # Si le groupe indiqué est un chemin contenant
                    # plusieurs composantes, par exemple: "A/B".
                    # Alors il est invalide ici.
                    parts = parse_path(ventilation)

                    # NB: parts peut valoir None si le parsing a échoué.
                    if ventilation and (not parts or len(parts) > 1):
                        raise ParsingError(_("Invalid ventilation group: %s") %
                            ventilation)

                    # On génère le nom de fichier relatif par rapport
                    # à la racine du checkout SVN.
                    cur_host = Host(
                        self.hosts,
                        source,
                        name,
                        address,
                        ventilation
                    )

                    self.hosttemplatefactory.apply(cur_host, "default")

                elif elem.tag == "nagios":
                    process_nagios = True

                elif elem.tag == "test":
                    test_name = get_attrib(elem, "name")
                    test_directives = {}

            else: # Événement de type "end"
                if elem.tag == "force-passive":
                    cur_host.set_attribute("force-passive", True)

                if elem.tag == "template":
                    templates.append(get_text(elem))

                elif elem.tag == "test":
                    test_name = get_attrib(elem, 'name')

                    args = {}
                    for arg in elem.getchildren():
                        if arg.tag != 'arg':
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
                    tests.append( (test_name, args, test_directives) )
                    test_name = None

                elif elem.tag == "attribute":
                    value = get_text(elem)
                    items = [ get_text(i) for i in elem.getchildren()
                              if i.tag == "item" ]
                    if items:
                        value = items
                    attributes[get_attrib(elem, 'name')] = value

                elif elem.tag == "tag":
                    service = None
                    if 'service' in elem.attrib:
                        service = get_attrib(elem, 'service')
                    tags.append( (service, get_attrib(elem, 'name'),
                                  get_text(elem)) )

                elif elem.tag == "directive":
                    if not process_nagios:
                        continue

                    dname = get_attrib(elem, 'name')
                    if not dname:
                        continue

                    dtarget = get_attrib(elem, 'target')
                    dvalue = get_text(elem)

                    if test_name is None:
                        # directive nagios générique pour un hôte ou sur
                        # l'ensemble des services (suivant la target)
                        directives[(dname, dtarget)] = dvalue
                    else:
                        # directive nagios spécifique à un service
                        test_directives[dname] = dvalue

                elif elem.tag == "group":
                    group_name = get_text(elem)
                    if not parse_path(group_name):
                        raise ParsingError(_('Invalid group name (%s)')
                            % group_name)
                    cur_host.add_group(group_name)

                elif elem.tag == "nagios":
                    process_nagios = False

                elif elem.tag == "host":
                    # On applique les attributs avant les templates, pour
                    # qu'ils soient dispo dans les tests des templates
                    for attr_name, attr_value in attributes.iteritems():
                        cur_host.set_attribute(attr_name, attr_value)

                    # On génère un graphe des dépendances de l'hôte
                    # en terme de templates.
                    g = self.hosttemplatefactory.templates_deps.copy()
                    g.add_node(None) # None représente l'hôte lui-même.
                    for template in templates:
                        g.add_edge(None, template)

                    try:
                        # On récupère le sous-graphe des dépendances relatives
                        # aux templates qui interviennent dans la configuration
                        # de cet hôte.
                        nodes = g.subgraph(
                            nx.dijkstra_predecessor_and_distance(g, None)
                                [1].keys()
                        )

                        # On ajoute des dépendances au graphe correspondant
                        # à l'ordre d'apparition des templates dans la
                        # configuration de l'hôte.
                        for i in xrange(len(templates) - 1):
                            try:
                                nx.shortest_path_length(
                                    nodes,
                                    templates[i],
                                    templates[i + 1]
                                )
                            except nx.NetworkXException:
                                # Il n'y a pas de chemin entre les deux,
                                # donc pas de risque de créer un cycle.
                                g.add_edge(templates[i + 1], templates[i])
                            else:
                                LOGGER.warning(_(
                                    "Host '%(host)s' inherits from both the "
                                    "'%(tpl1)s' and '%(tpl2)s' templates "
                                    "(in this order), but '%(tpl1)s' already "
                                    "inherits from '%(tpl2)s'. The templates "
                                    "will be reordered to satisfy "
                                    "dependencies.") % {
                                        'host': cur_host.name,
                                        'tpl1': templates[i],
                                        'tpl2': templates[i + 1],
                                    }
                                )

                        # Puis on trie la liste par ordre inverse
                        # d'application des templates à suivre.
                        nodes = nx.topological_sort(nodes)

                        if nodes is None: # compatibilité networkx < 1.3
                            # message non traduit pour être aussi compatible
                            # que possible.
                            raise nx.NetworkXUnfeasible(
                                "Graph contains a cycle.")

                        # On rétablit le bon ordre.
                        nodes.reverse()
                    except nx.NetworkXUnfeasible:
                        raise ParsingError(_("Unable to load templates for "
                                            "%(host)s. Possible cycle.") % {
                                                'host': cur_host.name,
                                            })

                    # On applique tous les templates dans l'ordre :
                    # des parents aux enfants (en excluant l'hôte = None).
                    for template in nodes[:-1]:
                        # Le template "default" est déjà appliqué
                        # lorsqu'on tombe sur la balise ouvrante <host>.
                        if template == 'default':
                            continue
                        self.hosttemplatefactory.apply(cur_host, template)

                    # On ré-applique les attributs après les templates, au cas
                    # où ces derniers les auraient écrasés (c'est la définition
                    # dans l'hôte qui prime sur celle dans le template)
                    for attr_name, attr_value in attributes.iteritems():
                        cur_host.set_attribute(attr_name, attr_value)

                    if not len(cur_host.get_attribute('otherGroups')):
                        raise ParsingError(_('You must associate host "%s" '
                            'with at least one group.') % cur_host.name)

                    for test_params in tests:
                        testclass = self.testfactory.get_test(test_params[0])
                        if not testclass:
                            raise ParsingError(_("No such test '%(testname)s' "
                                    "on host %(hostname)s")
                                    % {"hostname": cur_host.name,
                                       "testname": test_params[0]})
                        cur_host.add_tests(testclass, *test_params[1:])

                    if cur_host.get_attribute("force-passive"):
                        cur_host.add_nagios_directive("use", "generic-passive-host")

                    for ((dname, dtarget), dvalue) in directives.iteritems():
                        cur_host.add_nagios_directive(dname, dvalue,
                                                      target=dtarget)

                    for (service, tagname, tagvalue) in tags:
                        cur_host.add_tag(service, tagname, tagvalue)

                    LOGGER.debug("Loaded host %(host)s, address %(address)s" %
                                 {'host': cur_host.name,
                                  'address': cur_host.get_attribute('address'),
                                 })
                    elem.clear()
                    cur_host = None

# vim:set expandtab tabstop=4 shiftwidth=4:
