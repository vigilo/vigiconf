#!/usr/bin/env python
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
This module contains the DBExportator, a tool to export
hosts and services configuration into the vigilo database.
"""

from __future__ import absolute_import

import sys
import syslog
import os

from vigilo.common.conf import settings
settings.load_module(__name__)

#from vigilo.models.session import DBSession
from vigilo.models.configure import DBSession

from vigilo.models import Host, HostGroup, LowLevelService, ServiceGroup
from vigilo.models import Graph, GraphGroup
from vigilo.models import Application, Ventilation, VigiloServer
from vigilo.models import ConfItem

from . import conf

# chargement de données xml
from vigilo.vigiconf.loaders import hostgrouploader,\
                                    servicegrouploader,\
                                    dependencyloader,\
                                    hlserviceloader

__docformat__ = "epytext"


def update_apps_db():
    """ Update database with new apps.
    """
    apps = conf.apps
    
    # apps
    for name in apps.keys():
        app = Application.by_app_name(name)
        if not app:
            app = Application(name=unicode(name))
            DBSession.add(app)
    
    DBSession.flush()

def export_conf_db():
    """ Update database with hostConf data.
    @returns: None
    """
    hostsConf = conf.hostsConf
    hostsGroups = conf.hostsGroups
    
    # groups for new entities
    group_newhosts_def = settings['vigiconf'].get('GROUPS_DEF_NEW_HOSTS',
                                          u'new_hosts_to_ventilate')
    group_newservices_def = settings['vigiconf'].get('GROUPS_DEF_NEW_SERVICES',
                                          u'new_services')
    
    # add if needed these groups
    if not HostGroup.by_group_name(group_newhosts_def):
        DBSession.add(HostGroup(name=unicode(group_newhosts_def)))
    
    if not ServiceGroup.by_group_name(group_newservices_def):
        DBSession.add(ServiceGroup(name=unicode(group_newservices_def)))
    group_newservices_def = ServiceGroup.by_group_name(group_newservices_def)
    
    # hosts groups
    try:
        for name in hostsGroups.keys():
            hg = HostGroup.by_group_name(name)
            if not hg:
                hg = HostGroup(name=unicode(name))
            DBSession.add(hg)
        DBSession.flush()
    except:
        raise
    
    # hosts
    try:
        for hostname, host in hostsConf.iteritems():
            h = Host.by_host_name(hostname)
            if h:
                # update host object
                h.checkhostcmd = host['checkHostCMD']
                h.hosttpl = host['hostTPL']
                h.snmpcommunity = host['community']
                h.snmpoidsperpdu = host['snmpOIDsPerPDU']
                h.snmpversion = host['snmpVersion']
                h.mainip = host['mainIP']
                h.snmpport = host['port']
                # add groups to host
                h.groups = [HostGroup.by_group_name(host['serverGroup']), ]
            else:
                # create host object
                h = Host(name=unicode(hostname),
                         checkhostcmd=host['checkHostCMD'],
                         hosttpl=host['hostTPL'],
                        snmpcommunity=host['community'],
                        mainip=host['mainIP'], snmpport=host['port'],
                        snmpoidsperpdu=host['snmpOIDsPerPDU'], weight=1,
                        snmpversion=host['snmpVersion'])
                DBSession.add(h)
                h.groups = [HostGroup.by_group_name(group_newhosts_def), ]
            
            # low level services
            # TODO: implémenter les détails: op_dep, weight, command
            
            for service in host['services'].keys():
                lls = LowLevelService.by_host_service_name(hostname, service)
                if not lls:
                    lls = LowLevelService(host=h, servicename=unicode(service),
                                          op_dep=u'+', weight=1)
                    lls.groups = [group_newservices_def, ]
                    DBSession.add(lls)
                # nagios generic directives for services
                if host['nagiosSrvDirs'].has_key(service):
                    for name, value in host['nagiosSrvDirs'][service].iteritems():
                        ci = ConfItem.by_host_service_confitem_name(hostname, service, name)
                        if ci:
                            ci.value = value
                        else:
                            ci = ConfItem(supitem=lls, name=name, value=value)
                            DBSession.add(ci)
            
            # nagios generic directives for host
            for name, value in host['nagiosDirectives'].iteritems():
                ci = ConfItem.by_host_confitem_name(hostname, name)
                if ci:
                    ci.value = value
                else:
                    ci = ConfItem(supitem=h, name=name, value=value)
                    DBSession.add(ci)
            
            
            for og in host['otherGroups']:
                h.groups.append(HostGroup.by_group_name(og))
            
            # export graphes groups
            _export_host_graphgroups(host['graphGroups'], h)
            
            # export graphes
            _export_host_graphitems(host['graphItems'], h)
            
        DBSession.flush()
    except:
        raise
    
    
    DBSession.flush()
    
    confdir = settings['vigiconf'].get('confdir')
    # hiérarchie groupes hosts (fichier xml)
    hostgrouploader.load_dir(os.path.join(confdir, 'hostgroups'), delete_all=True)
    
    # TODO: refactoring à prévoir
    # les groupes se chargent maintenant avec loader XML
    conf.hostsGroups = hostgrouploader.get_hosts_conf()
    conf.groupsHierarchy = hostgrouploader.get_groups_hierarchy()
    
    # hiérarchies groupes services
    servicegrouploader.load_dir(os.path.join(confdir, 'servicegroups'), delete_all=True)
    
    # high level services
    hlserviceloader.load_dir(os.path.join(confdir, 'hlservices'), delete_all=True)
    
    # dépendances
    dependencyloader.reset_change()
    dependencyloader.load_dir(os.path.join(confdir, 'dependencies'), delete_all=True)
    dependencyloader.detect_change()

def _export_host_graphgroups(graphgroups, h):
    """
    Update database with graph groups for a host.
    
    TODO: lien avec host ?
    
    @param graphgroups: a dict describing the graph groups hierarchy for a host
    @type graphgroups: C{dict}
    @param h: host
    @param h: C{Host}
    @returns: None
    """
    # reset hierarchy
    for graph in DBSession.query(Graph):
        graph.groups = []
        
    for groupname, graphnames in graphgroups.iteritems():
        group = GraphGroup.by_group_name(groupname)
        if group:
            group.children = [] # redundant with graph.groups = [] ?
        else:
            group = GraphGroup(name=unicode(groupname))
            DBSession.add(group)
        for name in graphnames:
            graph = DBSession.query(Graph).filter(Graph.name == name).first()
            if not graph:
                graph = Graph(name=name, template=u'lines', vlabel=u'unknown')
            graph.groups.append(group)
    
    DBSession.flush()
        


def _export_host_graphitems(graphitems, h):
    """
    Update database with graph items for a host.
    
    TODO: lien avec host ?
    
    @param graphitems: a dict describing the graph items for a host.
    @type graphitems: C{dict}
    @param h: host
    @param h: C{Host}
    @returns: None
    """
    for name, graph in graphitems.iteritems():
        g = DBSession.query(Graph).filter(Graph.name == name).first()
        g.template = graph['template']
        g.vlabel = graph['vlabel']
    
    DBSession.flush()


if __name__ == "__main__":
    syslog.openlog('DBExportator' , syslog.LOG_PERROR)
    syslog.syslog(syslog.LOG_INFO, "DBExportator Begin")

    try:
        conf.loadConf()
    except Exception, e :
        syslog.syslog(syslog.LOG_ERR, "Cannot load the conf.")
        syslog.syslog(syslog.LOG_ERR, str(e) )
        sys.exit(-1)

    export_conf_db()
    
    syslog.syslog(syslog.LOG_INFO, "DBExportator End")

def export_ventilation_DB(ventilation):
    """Export ventilation in DB
    @param ventilation: dict generated by findAServerForEachHost
    @type ventilation: C{dict}
    @returns: None
    
    Example:
      >>> findAServerForEachHost()
      {
      ...
      "my_host_name":
        {
          'apacheRP': 'presentation_server.domain.name',
          'collector': 'collect_server_pool1.domain.name',
          'corrsup': 'correlation_server.domain.name',
          'corrtrap': 'correlation_server.domain.name',
          'dns': 'infra_server.domain.name',
          'nagios': 'collect_server_pool1.domain.name',
          'nagvis': 'presentation_server.domain.name',
          'perfdata': 'collect_server_pool1.domain.name',
          'rrdgraph': 'store_server_pool2.domain.name',
          'storeme': 'store_server_pool2.domain.name',
          'supnav': 'presentation_server.domain.name'
        }
      ...
      }
    
    """
    # delete all associations
    DBSession.query(Ventilation).delete()
    
    for host, serverbyapp in ventilation.iteritems():
        for app, server in serverbyapp.iteritems():
            vigiloserver = VigiloServer.by_vigiloserver_name(server)
            
            if not vigiloserver:
                msg = "Vigilo server %s does not exists in db." % server
                syslog.syslog(syslog.LOG_ERR, msg)
                raise Exception(msg)
            
            v = Ventilation(host=Host.by_host_name(host),
                        vigiloserver=vigiloserver,
                        application=Application.by_app_name(app))
            
            DBSession.add(v)
    DBSession.flush()

