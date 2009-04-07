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
This module contains the Host class
"""

import base64

import conf
from lib.confclasses.graph import Graph

class Host(object):
    """
    The Host configuration class.

    This class defines all the attributes and the methods of hosts in the
    configuration system.

    The attributes are added to the hostsConf hashmap, and the methods
    directly modify this hashmap.

    The methods are used by the tests definitions.

    @ivar name: the hostname
    @type name: C{str}
    @ivar classes: the host classes
    @type classes: C{list} of C{str}
    """

    def __init__(self, name, ip, servergroup, **kw):
        self.name = name
        self.classes = [ "all" ]
        if kw.has_key("classes"):
            self.classes.extend(kw["classes"])
        if servergroup not in conf.groupsHierarchy:
            conf.groupsHierarchy[servergroup] = set()
        conf.hostsConf[name] = {
                "name": name,
                "fqhn": name,
                "mainIP": ip,
                "serverGroup": servergroup,
                "otherGroups": { servergroup: 1 },
                "services"       : {},
                "dataSources"    : {},
                "PDHandlers"     : {},
                "SNMPJobs"       : {},
                "graphItems"     : {},
                "routeItems"     : {},
                "trapItems"      : {},
                "graphGroups"    : {},
                "reports"        : {},
                "cti"            : 1,
                "hostTPL"        : "generic-active-host",
                "checkHostCMD"   : "check-host-alive",
                "snmpVersion"    : "2",
                "community"      : "public",
                "port"           : 161,
                "snmpOIDsPerPDU" : 10,
            }
        self.apply_template("default")
        conf.hostsConf[name].update(kw)

    def get_attribute(self, attribute, default=False):
        """
        A very simple wrapper to get a class attribute
        @param attribute: the attribute to get
        @param default: default value if the attribute is not found
        """
        return getattr( self, attribute, default )

    def add_test(self, testname, **kw):
        """
        Add a test to this host, with the provided arguments
        @param testname: the name of the test
        @type  testname: C{str}
        @param kw: the test arguments
        @type  kw: C{dict}
        """
        conf.testfactory.add_test(self, testname, **kw)

    def get_testnames(self):
        """
        @return: available test names for this host
        @rtype: C{set}
        """
        return conf.testfactory.get_testnames(self.classes)

    def apply_template(self, tpl):
        """
        Apply a host template to this host
        @param tpl: the template name
        @type  tpl: C{str}
        """
        conf.hosttemplatefactory.apply(self, tpl)

#### Access the global dicts ####

    def add_group(self, group_name):
        """
        Add the host to a new secondary group
        @param group_name: the group to be added to
        @type  group_name: C{str}
        """
        # This should really be a set(), but self.add only handles dicts
        self.add(self.name, "otherGroups", group_name, 1)
        # If the secondary group did not exist yet in the main group hashmap,
        # add it
        server_group = self.get("serverGroup")
        if group_name not in conf.groupsHierarchy[server_group]:
            conf.groupsHierarchy[server_group].add(group_name)

    def add_dependency(self, service="Host", deps=None, options=None, cti=1):
        """
        Add a topological dependency, from "origin" to "target".
        @param service: the origin service. If the value is the string "Host",
            then the host itself is the origin.
        @type  service: C{str}
        @param deps: the target dependencies. If deps is a C{str}, then it is
            considered as a hostname. If deps is a dict, then it may be of the
            following form::

                { 
                    "and": [(host1, "Host"), (host2, "Service1")]
                    "or": [(host3, "Host")]
                }

        @param options: TODO
        @type  options: C{list}
        @param cti: alert reference (Category - Type - Item)
        @type  cti: C{int}
        @todo: finish agument description
        """
        if deps is None:
            return
        if options is None:
            options = []
        if isinstance(deps, str) and deps != "":
            # target argument given as string
            deps = { "and": [(deps, "Host")] }
        conf.dependencies[(self.name, service)] = {"deps": {"and": [],
                                                            "or": []}, 
                                                   "options": options,
                                                   'cti': cti}
        for dep_type, dep_list in deps.iteritems():
            for dep in dep_list:
                if isinstance(dep, str):
                    dep = (dep, "Host")
                conf.dependencies[(self.name, service)]["deps"]\
                                                       [dep_type].append(dep)

#### Access the hostsConf dict ####

    def get(self, prop):
        """
        A generic function to get a property from the main hashmap
        @param prop: the property to get
        @type  prop: hashable
        """
        return conf.hostsConf[self.name][prop]

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
        if not conf.hostsConf[hostname].has_key(prop):
            conf.hostsConf[hostname][prop] = {}
        conf.hostsConf[hostname][prop].update({key: value})

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
        if not conf.hostsConf[hostname].has_key(prop):
            conf.hostsConf[hostname][prop] = {}
        if not conf.hostsConf[hostname][prop].has_key(subprop):
            conf.hostsConf[hostname][prop][subprop] = {}
        conf.hostsConf[hostname][prop][subprop].update({key: value})

    def add_trap(self, service, key, value):
        """
        Add an SNMP trap handler
        @param service: the SNMP trap service
        @type  service: C{str}
        @param key: the key to translate from
        @type  key: C{str}
        @param value: the value to translate to
        @type  value: C{str}
        """
        if (self.get("trapItems").has_key(service)):
            self.add_sub(self.name, "trapItems", service, key, value)
        else:
            self.add(self.name, "trapItems", service, {key: value})

#### Collector-related functions ####

    def add_collector_service(self, label, function, params, variables, cti=1,
                                    reroutefor=None, maxchecks=1):
        """
        Add a supervision service to the Collector
        @param label: the service display label
        @type  label: C{str}
        @param function: the Collector function to use
        @type  function: C{str}
        @param params: the parameters for the Collector function
        @type  params: C{str}
        @param variables: the variables for the Collector function
        @type  variables: C{list}
        @param cti: alert reference (Category - Type - Item)
        @type  cti: C{int}
        @param reroutefor: service routing information
        @type  reroutefor: C{dict} with "host" and "service" as keys
        @param maxchecks: the max number of checks before Nagios should
            send a notification
        @type  maxchecks: C{int}
        """
        # Handle rerouting
        if reroutefor == None:
            target = self.name
            service = label
        else:
            target = reroutefor["host"]
            service = reroutefor['service']
        # Add the Nagios service (rerouting-dependant)
        self.add(target, "services", service, {'type': 'passive', 
                                               'cti': cti, 
                                               'maxchecks': maxchecks,
                                              })
        # Add the Collector service (rerouting is handled inside the Collector)
        self.add(self.name, "SNMPJobs", (label, 'service'),
                                        {'function': function, 
                                         'params': params, 
                                         'vars': variables, 
                                         'reRouteFor': reroutefor,
                                         } )

    def add_collector_metro(self, name, function, params, variables, dstype,
                                  label=None, reroutefor=None):
        """
        Add a metrology datasource to the Collector
        @param name: the datasource name
        @type  name: C{str}
        @param function: the Collector function to use
        @type  function: C{str}
        @param params: the parameters for the Collector function
        @type  params: C{str}
        @param variables: the variables for the Collector function
        @type  variables: C{list}
        @param dstype: datasource type
        @type  dstype: "GAUGE" or "COUNTER", see RRDtool documentation
        @param label: the datasource display label
        @type  label: C{str}
        @param reroutefor: service routing information
        @type  reroutefor: C{dict} with "host" and "service" as keys
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
        self.add(target, "dataSources", service,
                 {'dsType':dstype, 'label': label})
        # Add the Collector service (rerouting is handled inside the Collector)
        self.add(self.name, "SNMPJobs", (name, 'perfData'),
                                        {'function': function,
                                         'params': params,
                                         'vars': variables,
                                         'reRouteFor': reroutefor,
                                         } )

    def add_collector_service_and_metro(self, name, label, supfunction,
                    supparams, supvars, metrofunction, metroparams, metrovars,
                    dstype, cti=1, reroutefor=None, maxchecks=1):
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
        @type  supparams: C{str}
        @param supvars: the variables for the Collector supervision function
        @type  supvars: C{list}
        @param metrofunction: the Collector function to use for metrology
        @type  metrofunction: C{str}
        @param metroparams: the parameters for the Collector metrology function
        @type  metroparams: C{str}
        @param metrovars: the variables for the Collector metrology function
        @type  metrovars: C{list}
        @param dstype: datasource type
        @type  dstype: "GAUGE" or "COUNTER", see RRDtool documentation
        @param cti: alert reference (Category - Type - Item)
        @type  cti: C{int}
        @param reroutefor: service routing information
        @type  reroutefor: C{dict} with "host" and "service" as keys
        @param maxchecks: the max number of checks before Nagios should
            send a notification
        @type  maxchecks: C{int}
        """
        self.add_collector_service(name, supfunction, supparams, supvars,
                        cti=cti, reroutefor=reroutefor, maxchecks=maxchecks)
        self.add_collector_metro(name, metrofunction, metroparams, metrovars, 
                                 dstype, label=label, reroutefor=reroutefor)

    def add_collector_service_and_metro_and_graph(self, name, label, oid,
            th1, th2, dstype, template, vlabel, supcaption=None,
            supfunction="thresholds_OID_simple", metrofunction="directValue",
            group="General", cti=1, reroutefor=None, maxchecks=1):
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
                    [], [ "GET/%s"%oid ], dstype, cti=cti,
                    reroutefor=reroutefor, maxchecks=maxchecks)
        if reroutefor != None:
            target = reroutefor['host']
            name = reroutefor['service']
        else:
            target = self.name
        graph = Graph(label, [ name ], template, vlabel, group=group)
        graph.add_to_host(target)

    def add_graph(self, title, dslist, template, vlabel,
                        group="General", factors=None):
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
        graph = Graph(title, dslist, template, vlabel,
                      group=group, factors=factors)
        graph.add_to_host(self.name)

    def add_to_graph(self, title, ds, factor=None):
        """
        Add the DS to an existing graph
        @param title: The graph title to add to
        @type  title: C{str}
        @param ds: The datasources to add
        @type  ds: C{str}
        @param factor: the factor to use, if any
        @type  factor: C{int} or C{float}
        """
        conf.hostsConf[self.name]["graphItems"][title]["ds"].append(ds)
        if factor is not None:
            conf.hostsConf[self.name]["graphItems"][title]["factors"]\
                                                                 [ds] = factor

    def add_report(self, title, reportname, datesetting=0):
        """
        Add a Report to an host 
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

    def add_external_sup_service(self, name, command, cti=1, maxchecks=1):
        """
        Add a standard Nagios service
        @param name: the service name
        @type  name: C{str}
        @param command: the command to use
        @type  command: C{str}
        @param cti: alert reference (Category - Type - Item)
        @type  cti: C{int}
        @param maxchecks: the max number of checks before Nagios should
            send a notification
        @type  maxchecks: C{int}
        """
        self.add(self.name, 'services', name, {'type': 'active',
                'command': command, 'cti': cti, 'maxchecks': maxchecks})
    
    def add_perfdata_handler(self, service, name, label, perfdatavarname,
                              dstype="GAUGE", reroutefor=None):
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
        """
        if reroutefor == None:
            target = self.name
        else:
            target = reroutefor['host']
        # Add the RRD
        self.add(target, "dataSources", service,
                 {'dsType': dstype, 'label': label})
        # Add the perfdata handler in Nagios
        if not self.get('PDHandlers').has_key(service):
            self.add(self.name, "PDHandlers", service, [])
        conf.hostsConf[self.name]['PDHandlers'][service].append(
                {'name': name, 'perfDataVarName': perfdatavarname,
                 'reRouteFor': reroutefor})

    def add_rrd_service(self, servicename, rrdname, warn, crit, factor=1):
        """
        Add a Nagios test on the values stored in a RRD file
        @param servicename: the name of the Nagios service
        @type  servicename: C{str}
        @param rrdname: the name of the rrd file
        @type  rrdname: C{str}
        @param warn: the WARNING threshold.
        @type  warn: C{str}
        @param crit: the CRITICAL threshold.
        @type  crit: C{str}
        @param factor: the factor to use, if any
        @type  factor: C{int} or C{float}
        """
        self.add_external_sup_service(servicename,
            "check_nrpe_rerouted!$METROSERVER$!check_rrd!%s/%s %s %s %s" % \
            (self.name, base64.b64encode(rrdname), warn, crit, factor)
        )

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
        if service == "Host" or service is None:
            target = conf.hostsConf[self.name]
        else:
            target = conf.hostsConf[self.name]["services"][service]
        if not target.has_key("tags"):
            target["tags"] = {}
        target["tags"][name] = value



# vim:set expandtab tabstop=4 shiftwidth=4:
