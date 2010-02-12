################################################################################
#
# ConfigMgr configuration loader
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
# pylint: disable-msg=C0103
"""
Description
===========

Configuration loader based on an execfile of a subdirectory 
containing .py files

This is the module that produces the whole data model of ConfMgr
and thus every other ConfMgr modules will use part of this data model

Data Model
==========
  This modules populates several dictionnaries:

  dependencies
  ------------
    This dictionnary containes the explicit dependencies that have been declared
    between hosts and/or services. See Graph.pm perldoc in Vigilo's CorrSup for
    more details

      - B{Key}: Keys are reprensented by a tuple (Host, service)
      - B{Value}: Value are a dictionnary with the following items:
          
        - I{cti}: the optional numbered cti classification of the event
        - I{options}: the options that apply to this dependency node:
          - I{virtual},
          - I{hide_this_impact},
          - I{weight=454}.
        - I{deps}: the dependency with other nodes. This is a usually a single
          entry dictionnary:
           - Key: the operator type that apply to this node
             (I{and}, I{or}, I{sum})
           - Value: the list of items that are tuples (host_name, service_name).
             Second tuple element can be omitted if equal to I{Host}.

    Example:
        >>> import pprint
        >>> pprint.pprint(dependencies)
        {('ajc.fw.1', 'Host'): {'cti': 1,
          'deps': {'and': [('proto4', 'Host')], 'or': []},
          'options': []},
        ('ajc.linux0', 'Host'): {'cti': 1,
          'deps': {'and': [('ajc.sw.1', 'Host')], 'or': []},
          'options': []},
        }

  groupsHierarchy
  ---------------
    This dictionnary describes a 2-level group tree
    Example:
      >>> import pprint
      >>> pprint.pprint groupsHierarchy
      {'Serveurs': {'Demo-Vigilo': 1,
            'Serveurs CS': 1,
            'Serveurs Linux': 1,
            'Serveurs Solaris': 1,
            'Serveurs Windows': 1},
      'Telecom': {'NORTEL': 1, 'Serveurs CS': 1}}

  hostsConf
  ---------
    This dictionnary contains all the host dependent 
    supvervision configuration:
      - B{Key}: The host name,
      - B{Value}: the host configuration (dict):
        - I{HostClasses}: the list of string describing the classes associated
          to the host. Often used in SNMP to guess how to test a feature
        - I{checkHostCMD}: the name of the nagios test command to check this
          host presence (Ping ?)
        - I{community}: an SNMP v1 or v2 community name, if applicable
        - I{cti}: the (Category Type Item) classification of this host
        - I{fqhn}: the Full Qualified Host Name (string)
        - I{hostTPL}: the Nagios template to use for this host
        - I{mainIP}: the main IP address to use when talking with this host
        - I{name}: short name of the host (must be unique)
        - I{serverGroup}: the main group this host belongs to. The ownership
          will determine the group of supervision servers on which it will be
          supervised
        - I{otherGroups}: dict {name: 1} of secondary groups the host belongs to
        - I{port}: the SNMP port of the host, is applicable
        - I{routeItems}: unused except in non standard cases (see Nagios
          generator)
        - I{snmpOIDsPerPDU}: The number of OID to send into a single SNMP PDU
          before fragmenting. Usually depends on the OS type.
        - I{snmpVersion}: the SNMP version (I{1}, I{2} or I{3})
        - I{dataSources}: the list of all data sources that are being collected
          and graphed. This is a dict:
            - B{Key}: the name of the Data source
            - B{Value}: a dict of the data source options:
              - I{dsType}: the type of the DS (in RRDtool terms) (I{GAUGE},
                I{COUNTER})
              - I{label}: a caption for this data source (string)
            - B{example}: C{{'sysUpTime':
                            {'dsType': 'GAUGE', 'label': 'UpTime'}}}
        - I{graphItems}: the definition of the graphes available for this host.
          A dict:
           - B{Key}: the name of the graph
           - B{Value}: a dict with all the internal attributes of this graph:
             - I{ds}: the list of datasources (named as the keys of the
               I{datasources} dict) B{order matters}
             - I{factors}: a dict (ds_name, float) of the multiplication factor
               to apply to one or more DSs
             - I{template}: the name (string) of the RRDGraph representaiton
               template to use for this graph (I{lines}, I{stacks})
             - I{vlabel}: the vertical caption (string) to put on the y scale
             - B{example}: 

               >>> hostsConf['my_host']['graphItems']['Host Load']
               {
                 'ds': ['Load 01', 'Load 05', 'Load 15'],
                 'factors': {'Load 01': 0.01, 'Load 05': 0.01, 'Load 15': 0.01},
                 'template': 'areas',
                 'vlabel': 'load'
               }

        - I{graphGroups}: a 2-level hierarchy storing graphes into
          sub-categories {group_name : {graph_name : 1}}
        - I{PDHandlers}: dict of Nagios perfdata handling strategy:
          - B{Key}: the service Name
          - B{Value}: a list of dict:
            - I{name}: the DS name(this name is supposed to be present into the
              I{dataSources} (see above) dict and referenced by a graph for
              this host to be of any use)
            - I{perfDataVarName}: the name of the variable produced by the
              Nagios plugin
            - I{reRouteFor}: None or a tuple (host, service) where to reroute
              this perfdata to
          - B{example}:

            >>> hostsConf['my_host']['PDHandlers']
            {
                'PDHandlers': {'HTTP': [{'name': 'HTTP-time',
                    'perfDataVarName': 'time',
                    'reRouteFor': None}]},
            }

        - I{services}: a dict of the services (in Nagios language) that are
          present on this host. They can be active or passive.  Active services
          are bound to a Nagios plugin, Passive are usually fed using SpoolMe
          by a Collector instance for this host and sometime from a Collector
          from another host (when rerouting occurs), or completely externaly.
            - B{Key}: the service name (string) as shown in Nagios
            - B{Value}: a dict of this service's options:
              - I{cti}: the CTI of this service
              - I{maxchecks}: the number of checks to perform before notifying
                a failure (usually, 1)
              - I{type}: I{active} or I{passive}
              - I{command}: the Nagios command to launch for this B{active}
                service (I{check_nrpe_1arg!check_raid})
            - B{example}:

            >>> hostsConf['my_host']['services']
            {
            ...
                'RAID': {
                    'command': 'check_nrpe_1arg!check_raid',
                    'cti': 1,
                    'maxchecks': 1,
                    'type': 'active'
                },
                'TCP connections': {
                    'cti': 1,
                    'maxchecks': 1,
                    'type': 'passive'
                },
            ...
            }

        - I{SNMPJobs}: a dict containing the jobs that the Vigilo Collector
          plugin will have to perform:
           - B{Key}: a tuple in the form (service_name, 'service') or (ds_name,
             'perfData') depending on whether this job will produce a service
             (Nagios) output or a performance (RRD) data
           - B{Value}: a dict of this job's options:
             - I{function} the name of the Collector's function to call (as
               defined in the Functions.pm Collector library)
             - I{params}: a list of paramaters to provide to the I{function}
             - I{vars}: a list of SNMP GETs and WALKs needed to feed the
               I{function} with enough data
             - I{reRouteFor}: a tuple (host_name, service_name) in case of
               result rerouting
          B{example}:

            >>> hostsconf['my_host'][SNMPJobs']
            {
            ...
                ('Load 15', 'perfData'): {'function':
                        'directValue',
                        'params': [],
                        'reRouteFor': None,
                        'vars': ['GET/.1.3.6.1.4.1.2021.10.1.5.3']},
                ('Partition /boot', 'service'): {'function':
                        'storage',
                        'params': ['/boot',
                                   80,
                                   95,
                                   1],
                        'reRouteFor': None,
                        'vars': ['WALK/.1.3.6.1.2.1.25.2.3.1.3',
                                 'WALK/.1.3.6.1.2.1.25.2.3.1.4',
                                 'WALK/.1.3.6.1.2.1.25.2.3.1.5',
                                 'WALK/.1.3.6.1.2.1.25.2.3.1.6']},
            ...
            }

        - B{TODO: comment this} I{trapItems}: {'172.17.103.144.interfaces':
          {'eth0': 'Prod','lo': 'Loopback'}}

  dynamicGroups
  -------------
    This dictionnary contains the definition of dynamic groups. Dynamic groups
    are mostly used by nagvis to create custom maps, containing 3 kinds of
    items:
      - hostgroups
      - hosts
      - services
    To populate such maps, from 1 and up to 3 queries can be specified. Query
    are python expressions whose evaluation will determine whether a host,
    group or service belongs to a given map.
    The content of the dict is:
      - B{Key}: the label of the map
      - B{Value}: a dict describing the content of the map:
        - I{label}: the name of the map, supposed to equal the B{Key}.
        - I{show_in_main}: True to list this map into the main Nagvis map.
        - I{nagvis_server}: the nagvis server name where to put this map
        - I{host_query}: the python compliant expression to compute the hosts
          in this map or None
        - I{service_query}: the python compliant expression to compute the
          services in this map or None
        - I{group_query}: the python compliant expression to compute the
          hostgroups in this map or None
"""

from __future__ import absolute_import

import glob
import sys
import os
import subprocess

from vigilo.common.conf import settings
# TODO: Yuck ! :(
#settings.load_file("/home/esimorre/vigilo-base/vigiconf/settings_tests.ini")

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from .lib import ParsingError
from .lib.confclasses.host import HostFactory
from .lib.confclasses.hosttemplate import HostTemplateFactory
from .lib.confclasses.test import TestFactory


__docformat__ = "epytext"


def loadConf():
    """
    Load the confdir directory, looking for configuration files.
    @returns: None, but sets global variables as described above.
    """
    global hostsConf, groupsHierarchy
    # General configuration
    for confsubdir in [ "general", ]:
        try:
            files = glob.glob(os.path.join(settings["vigiconf"].get("confdir"),
                                           confsubdir, "*.py"))
            #print files
            for fileF in files:
                execfile(fileF, globals())
                #print "Sucessfully parsed %s"%fileF
        except Exception,e:
            sys.stderr.write("Error while parsing %s: %s\n"%(fileF, str(e)))
            raise e
    # Parse hosts
    try:
        hostfactory.load()
    except ParsingError, e:
        LOGGER.error("Error loading configuration file %s: %s\n"
                % (f.replace(os.path.join(settings["vigiconf"].get("confdir"),
                                          "hosts")+"/", ""), str(e)))
        raise e
    hostsConf = hostfactory.hosts
    groupsHierarchy = hostfactory.groupsHierarchy



# Initialize global paths
CODEDIR = os.path.dirname(__file__)

# Initialize global conf variables
apps = {}
appsByAppGroups = {}
hostsGroups     = {}
groupsHierarchy = {}
hostsConf = {}
dependencies = {}
dynamicGroups = {}
dns = {}
notificationServers = {}
defaultNotificationServer = "127.0.0.1:50003"
mode = "onedir"
#mode = "byday"
confid = ""

# Initialize global objects and only use those
testfactory = TestFactory()
hosttemplatefactory = HostTemplateFactory(testfactory)
hostfactory = HostFactory(
                os.path.join(settings["vigiconf"].get("confdir"), "hosts"),
                hosttemplatefactory,
                testfactory,
                groupsHierarchy,
              )


# vim:set expandtab tabstop=4 shiftwidth=4:
