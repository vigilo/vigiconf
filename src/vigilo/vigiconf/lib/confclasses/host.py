# -*- coding: utf-8 -*-
################################################################################
#
# Copyright (C) 2007-2012 CS-SI
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
This module contains the Host class
"""

from __future__ import absolute_import

import os
import inspect
from lxml import etree
from vigilo.common.nx import networkx as nx

#from vigilo.common.conf import settings
from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate, translate_narrow
_ = translate(__name__)
N_ = translate_narrow(__name__)

from . import get_text, get_attrib, parse_path
from .graph import Graph, Cdef
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
    @ivar classes: the host classes
    @type classes: C{list} of C{str}
    """

    def __init__(self, hosts, filename, name, address, servergroup):
        self.hosts = hosts
        self.name = name
        self.classes = [ "all" ]
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
                "trapItems"      : {},
                "snmpTrap"       : {},
                "netflow"        : {},
                "graphGroups"    : {},
                "reports"        : {},
                "hostTPL"        : "generic-active-host",
                "snmpVersion"    : "2",
                "snmpCommunity"  : "public",
                "snmpPort"       : 161,
                "snmpOIDsPerPDU" : 10,
                "nagiosDirectives": {
                    "host": {"check_command": "check-host-alive"},
                    "services": {},
                },
                "nagiosSrvDirs"  : {},
                "weight"         : 1,
                "force-passive"  : False,
            }
        self.attr_types = {"snmpPort": int,
                           "snmpOIDsPerPDU": int,
                           "weight": int,
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

    def _get_warning_weight(self, label, weight, warning_weight):
        """
        Retourne le poids à utiliser pour un service lorsqu'il passe
        dans l'état WARNING.

        @param label: Nom du service dans Nagios.
        @type label: C{str}
        @param weight: Poids du service lorsqu'il se trouve dans
            l'état OK ou UNKNOWN.
        @type weight: C{int}
        @param warning_weight: Poids indicatif demandé par l'utilisateur
            pour ce service lorsqu'il se trouve dans l'état WARNING.
            Si C{None} est passé comme valeur, la valeur par défaut est
            renvoyée (ie. la valeur de C{weight}).
        @type warning_weight: C{int} or None
        @return: Valeur effective du poids de ce service lorsqu'il
            se trouve dans l'état WARNING.
        @rtype: C{int}
        """
        if warning_weight is None:
            return weight

        if warning_weight > weight:
            raise ParsingError(_("warning_weight (%(warning_weight)d) must be "
                                "less than or equal to weight (%(weight)d) "
                                "for test '%(test)s' on host '%(host)s'") % {
                                    'test': label,
                                    'host': self.name,
                                    'warning_weight': warning_weight,
                                    'weight': weight,
                                })
        return warning_weight


    def add_tests(self, test_list, args=None,
                    weight=None, warning_weight=None,
                    directives=None):
        """
        Add a list of tests to this host, with the provided arguments

        @param test_list: the list of tests
        @type  test_list: C{list} of C{Test<.test.Test>}
        @param args: the test arguments
        @type  args: C{dict}
        @param weight: the test weight when in the OK state
        @type  weight: C{int}
        @param warning_weight: the test weight when in the WARNING state
        @type  warning_weight: C{int}
        """
        if weight is None:
            weight = 1

        warning_weight = self._get_warning_weight('', weight, warning_weight)

        if directives is None:
            directives = {}
        if args is None:
            args = {}
        for test_class in test_list:
            inst = test_class()
            try:
                inst.directives = directives
                inst.weight = weight
                inst.warning_weight = warning_weight
                inst.add_test(self, **args)
            except TypeError:
                spec = inspect.getargspec(inst.add_test)
                # On récupère la liste des arguments obligatoires.
                defaults = spec[3]
                if defaults is None:
                    args = spec[0][2:]
                else:
                    args = spec[0][2:-len(defaults)]
                message = _('Test "%(test_name)s" on "%(host)s" needs the '
                            'following arguments: %(args)s (and only those)') \
                          % {'test_name': str(test_class.__name__),
                             'host': self.name,
                             'args': ', '.join(args),
                            }
                raise VigiConfError(message)

#    def apply_template(self, tpl):
#        """
#        Apply a host template to this host
#        @param tpl: the template name
#        @type  tpl: C{str}
#        """
#        conf.hosttemplatefactory.apply(self, tpl)


#### Access the global dicts ####

    def add_group(self, group_name):
        """
        Add the host to a new secondary group
        @param group_name: the group to be added to
        @type  group_name: C{str}
        """
        group_name = unicode(group_name)
        self.hosts[self.name]['otherGroups'].add(group_name)

    def add_class(self, class_name):
        """
        Add a class to the host
        @param class_name: the class name to be added to
        @type  class_name: C{str}
        """
        if self.classes.count(class_name) == 0:
            self.classes.append(class_name)

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

    def add_trap(self, service, oid, data=None):
        """
        Add a SNMPT Trap handler (for snmptt).
        @param service: the service description (nagios service)
        @type service: C{str}
        @param oid: as name. For identify snmp trap.
        @type oid: C{str}
        @param data: the dictionnary contains :
            path to script to execute C{str},
            label: snmp trap event name C{str}
            address: ip address to match in snmptt C{str}
            service: service description (nagios service) C{str} (to remove?)
        @type data: C{dict}
        """
        if data is None:
            data = {}
        if not self.hosts[self.name].has_key("snmpTrap"):
            self.hosts[self.name]["snmpTrap"] = {}
        if not self.hosts[self.name]["snmpTrap"].has_key(service):
            self.hosts[self.name]["snmpTrap"][service] = {}
        self.hosts[self.name]["snmpTrap"][service][oid] = {}

        if not "address" in data.keys():
            data["address"] = self.hosts[self.name]["address"]
        for key, value in data.iteritems():
            self.hosts[self.name]["snmpTrap"][service][oid].update({key: value})

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
                              reroutefor=None, weight=1, warning_weight=None,
                              directives=None):
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
        @param weight: service weight when in the OK state
        @type  weight: C{int}
        @param warning_weight: service weight when in the WARNING state
        @type  warning_weight: C{int}
        """
        # Handle rerouting
        if reroutefor == None:
            target = self.name
            service = label
            reroutedby = None
        else:
            target = reroutefor["host"]
            service = reroutefor['service']
            reroutedby = {
                'host': self.name,
                'service': label,
            }

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
            'weight': weight,
            'warning_weight': self._get_warning_weight(
                                service, weight, warning_weight),
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

    def add_collector_service_and_metro(self, name, label, supfunction,
                    supparams, supvars, metrofunction, metroparams, metrovars,
                    dstype, reroutefor=None, weight=1, warning_weight=None,
                    directives=None):
        """
        Helper function for L{add_collector_service}() and
        L{add_collector_metro}().
        @param name: the service and datasource name
        @type  name: C{str}
        @param label: the service and datasource display label
        @type  label: C{str}
        @param supfunction: the Collector function to use for supervision
        @type  supfunction: C{str}
        @param supparams: the parameters for the Collector supervision function
        @type  supparams: C{list}
        @param supvars: the variables for the Collector supervision function
        @type  supvars: C{list}
        @param metrofunction: the Collector function to use for metrology
        @type  metrofunction: C{str}
        @param metroparams: the parameters for the Collector metrology function
        @type  metroparams: C{list}
        @param metrovars: the variables for the Collector metrology function
        @type  metrovars: C{list}
        @param dstype: datasource type
        @type  dstype: "GAUGE" or "COUNTER", see RRDtool documentation
        @param reroutefor: service routing information
        @type  reroutefor: C{dict} with "host" and "service" as keys
        @param weight: service weight when in the OK state
        @type  weight: C{int}
        @param warning_weight: service weight when in the WARNING state
        @type  warning_weight: C{int}
        """
        self.add_collector_service(name, supfunction, supparams, supvars,
                        reroutefor=reroutefor, weight=weight,
                        warning_weight=warning_weight, directives=directives)
        self.add_collector_metro(name, metrofunction, metroparams, metrovars,
                                 dstype, label=label, reroutefor=reroutefor)

    def add_collector_service_and_metro_and_graph(self, name, label, oid,
            th1, th2, dstype, template, vlabel, supcaption=None,
            supfunction="thresholds_OID_simple", metrofunction="directValue",
            group="General", reroutefor=None, weight=1, warning_weight=None,
            directives=None):
        """
        Helper function for L{add_collector_service}(),
        L{add_collector_metro}() and L{add_graph}(). See those methods for
        argument details
        """
        if not label:
            label = name
        if supcaption is None:
            supcaption = "%s: %%s" % label
        self.add_collector_service_and_metro(name, label, supfunction,
                    [th1, th2, supcaption], ["GET/%s"%oid], metrofunction,
                    [], [ "GET/%s"%oid ], dstype,
                    reroutefor=reroutefor,
                    weight=weight,
                    warning_weight=warning_weight,
                    directives=directives)
        if reroutefor != None:
            target = reroutefor['host']
            name = reroutefor['service']
        else:
            target = self.name
        graph = Graph(self.hosts, unicode(label), [ unicode(name) ],
                      unicode(template), unicode(vlabel), group=unicode(group))
        graph.add_to_host(target)

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
        except (UnicodeEncodeError, UnicodeDecodeError), e:
            try:
                errmsg = unicode(e)
            except UnicodeDecodeError:
                errmsg = unicode(str(e), 'utf-8', 'replace')
            raise VigiConfError(_("CDEF name must be ASCII-only: %s")
                                % errmsg)

    def add_report(self, title, reportname, datesetting=0):
        """
        Add a Report to an host
        @deprecated: This function is not used anymore in Vigilo V2.
        @param title: Specify a title into SupNavigator
        @type  title: C{str}
        @param reportname: The name of the report with extension
        @type  reportname: C{str}
        @param datesetting: The number of days to report
        @type  datesetting: C{str}
        """
        if title is not None and title not in self.get("reports"):
            self.add(self.name, "reports", title, {"reportName": reportname,
                                                   "dateSetting": datesetting})

    def add_external_sup_service(self, name, command=None,
                                 weight=1, warning_weight=None,
                                 directives=None):
        """
        Add a standard Nagios service
        @param name: the service name
        @type  name: C{str}
        @param command: the command to use
        @type  command: C{str}
        @param weight: service weight when in the OK state
        @type  weight: C{int}
        @param warning_weight: service weight when in the WARNING state
        @type  warning_weight: C{int}
        """
        if directives is None:
            directives = {}
        for (dname, dvalue) in directives.iteritems():
            self.add_sub(self.name, "nagiosSrvDirs", name, dname, dvalue)

        definition =  {'command': command,
                       'weight': weight,
                       'warning_weight': self._get_warning_weight(
                                            name, weight, warning_weight),
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

    def add_custom_service(self, name, stype, weight=1, warning_weight=None,
                            directives=None):
        """
        Ajoute un service Nagios quasiment entièrement défini par un des
        modèles fournis dans le générateur Nagios.
        Exemples: metro, connector.
        @param name: the service name
        @type  name: C{str}
        @param stype: the service type
        @type  stype: C{str}
        @param weight: service weight when in the OK state
        @type  weight: C{int}
        @param warning_weight: service weight when in the WARNING state
        @type  warning_weight: C{int}
        """
        if directives is None:
            directives = {}
        for (dname, dvalue) in directives.iteritems():
            self.add_sub(self.name, "nagiosSrvDirs", name, dname, dvalue)

        definition =  {'type': stype,
                       'weight': weight,
                       'warning_weight': self._get_warning_weight(
                                            name, weight, warning_weight),
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
                          factor=1, weight=1, warning_weight=None):
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
        """
        # Ajout du service Nagios
        self.add_custom_service(servicename, "metro",
                                weight=weight, warning_weight=warning_weight)
        # Ajout des seuils pour le connector-metro.
        self.add(self.name, "metro_services", metroname, {
            'servicename': servicename,
            'warning': warn,
            'critical': crit,
            'factor': factor,
        })

    def add_tag(self, service, name, value):
        """
        Add a tag to a host or a service. This tag is associated with a value.
        @param service: the service to add the tag to. If it is the string
            "Host", then the tag is added to the host itself.
        @type  service: C{str}
        @param name: the tag name
        @type  name: C{str}
        @param value: the tag value
        @type  value: C{int}
        """
        if not service or service.lower() == "host":
            target = self.hosts[self.name]
        else:
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

    def _validatehost(self, source, xsd): # pylint: disable-msg=R0201
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
        weight = None
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
                    weight = None
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

                elif elem.tag == "class":
                    cur_host.classes.append(get_text(elem))

                elif elem.tag == "test":
                    test_weight = get_attrib(elem, 'weight')
                    try:
                        test_weight = int(test_weight)
                    except ValueError:
                        raise ParsingError(
                            _("Invalid value for weight in test %(test)s "
                                "on host %(host)s: %(weight)r") % {
                                'test': test_name,
                                'host': cur_host.name,
                                'weight': test_weight,
                            })
                    except TypeError:
                        # C'est None, on laisse prendre la valeur par défaut
                        pass

                    test_warn_weight = get_attrib(elem, 'warning_weight')
                    try:
                        test_warn_weight = int(test_warn_weight)
                    except ValueError:
                        raise ParsingError(
                            _("Invalid value for warning_weight in test "
                                "%(test)s on host %(host)s: %(warning_weight)r"
                              ) % {
                                'test': test_name,
                                'host': cur_host.name,
                                'warning_weight': test_warn_weight,
                            })
                    except TypeError:
                        # C'est None, on laisse prendre la valeur par défaut
                        pass

                    args = {}
                    for arg in elem.getchildren():
                        if arg.tag == 'arg':
                            args[get_attrib(arg, 'name')] = get_text(arg)
                    tests.append( (test_name, args, test_weight,
                                   test_warn_weight, test_directives) )
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
                    dname = get_attrib(elem, 'name').strip()
                    if not dname:
                        continue

                    dtarget = get_attrib(elem, 'target')
                    if dtarget is not None:
                        dtarget= dtarget.strip()
                    dvalue = get_text(elem).strip()

                    # directive nagios générique pour un hôte ou sur
                    # l'ensemble des services (suivant la target)
                    if test_name is None:
                        cur_host.add_nagios_directive(dname, dvalue, target=dtarget)
                        continue

                    # directive nagios spécifique à un service
                    test_directives[dname] = dvalue

                elif elem.tag == "group":
                    group_name = get_text(elem)
                    if not parse_path(group_name):
                        raise ParsingError(_('Invalid group name (%s)')
                            % group_name)
                    cur_host.add_group(group_name)

                elif elem.tag == "weight":
                    host_weight = get_text(elem)
                    try:
                        weight = int(host_weight)
                    except ValueError:
                        raise ParsingError(_("Invalid weight value for "
                            "host %(host)s: %(weight)r") % {
                            'host': cur_host.name,
                            'weight': host_weight,
                        })
                    except TypeError:
                        # C'est None, on laisse prendre la valeur par défaut
                        pass

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
                        self.hosttemplatefactory.apply(cur_host, template)

                    # On ré-applique les attributs après les templates, au cas
                    # où ces derniers les auraient écrasés (c'est la définition
                    # dans l'hôte qui prime sur celle dans le template)
                    for attr_name, attr_value in attributes.iteritems():
                        cur_host.set_attribute(attr_name, attr_value)

                    if not len(cur_host.get_attribute('otherGroups')):
                        raise ParsingError(_('You must associate host "%s" '
                            'with at least one group.') % cur_host.name)

                    if weight is not None:
                        cur_host.set_attribute("weight", weight)

                    for test_params in tests:
                        test_list = self.testfactory.get_test(test_params[0],
                                          cur_host.classes)
                        if not test_list:
                            raise ParsingError(_("Can't add test %(testname)s "
                                    "to host %(hostname)s. Maybe a missing "
                                    "host class ?")
                                    % {"hostname": cur_host.name,
                                       "testname": test_params[0]})
                        cur_host.add_tests(test_list, *test_params[1:])

                    for (dname, dvalue) in directives.iteritems():
                        cur_host.add_nagios_directive(dname, dvalue)

                    for (service, tagname, tagvalue) in tags:
                        cur_host.add_tag(service, tagname, tagvalue)

                    if cur_host.get_attribute("force-passive"):
                        cur_host.set_attribute("hostTPL", "generic-passive-host")
                    LOGGER.debug("Loaded host %(host)s, address %(address)s" %
                                 {'host': cur_host.name,
                                  'address': cur_host.get_attribute('address'),
                                 })
                    elem.clear()
                    cur_host = None

# vim:set expandtab tabstop=4 shiftwidth=4:
