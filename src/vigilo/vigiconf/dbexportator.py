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
Ce module contient des fonctions permettant d'exporter dans la base
de données vigilo certaines données de configuration.

 * update_apps_db
   exporte en base les noms des applications

 * export_conf_db
   exporte en base les données groupes, les hôtes et les services de bas
   niveaux, les groupes de graphes, les services de haut niveau, les
   dépendances.
   
 * export_ventilation_DB
   exporte en base les données la ventilation des hôtes par application
   sur les serveurs de supervision.
"""

from __future__ import absolute_import

import sys
import syslog
import os

from vigilo.common.conf import settings
settings.load_module(__name__)

from vigilo.models.session import DBSession

from vigilo.models.tables import Host, SupItemGroup, LowLevelService
from vigilo.models.tables import Graph, GraphGroup, PerfDataSource
from vigilo.models.tables import Application, Ventilation, VigiloServer
from vigilo.models.tables import ConfItem

from .lib.dbupdater import DBUpdater, DBUpdater2

from . import conf

# chargement de données xml
from vigilo.vigiconf.loaders import grouploader,\
                                    dependencyloader,\
                                    hlserviceloader

__docformat__ = "epytext"


def update_apps_db():
    """ Update database with new apps.
    """
    apps = conf.apps
    
    # apps
    for name in apps.keys():
        app = Application.by_app_name(unicode(name))
        if not app:
            app = Application(name=unicode(name))
            DBSession.add(app)
    
    DBSession.flush()

def export_conf_db():
    """ Update database with hostConf data.
    """
    hostsConf = conf.hostsConf
    hostsGroups = conf.hostsGroups
    
    """# mise à jour des serveurs de supervision
    for app, dic in conf.appsGroupsByServer.iteritems():
        for appgroup, servers in dic.iteritems():
            servername = conf.appsGroupsByServer[appGroup][hostGroup]
        
        if not VigiloServer.by_vigiloserver_name(servername):
            server = VigiloServer(name=servername)
            DBSession.add(server)
    DBSession.flush()
    """
    confdir = settings['vigiconf'].get('confdir')
    # hiérarchie groupes hosts (fichier xml)
    # en premier, pour éviter d'effacer les groupes déclarés dans les hosts.
    grouploader.load_dir(os.path.join(confdir, 'groups'), delete_all=True)
    
    # TODO: refactoring à prévoir
    # les groupes se chargent maintenant avec loader XML
    conf.hostsGroups = grouploader.get_hosts_conf()
    conf.groupsHierarchy = grouploader.get_groups_hierarchy()
    
    # groups for new entities
    group_newhosts_def = unicode(settings['vigiconf'].get('GROUPS_DEF_NEW_HOSTS',
                                          u'new_hosts_to_ventilate'))
    group_newservices_def = unicode(settings['vigiconf'].get('GROUPS_DEF_NEW_SERVICES',
                                          u'new_services'))
    
    # add if needed these groups
    if not SupItemGroup.by_group_name(group_newhosts_def):
        DBSession.add(SupItemGroup.create(name=group_newhosts_def))
    group_newhosts_def = SupItemGroup.by_group_name(group_newhosts_def)
        
    if not SupItemGroup.by_group_name(group_newservices_def):
        DBSession.add(SupItemGroup.create(name=group_newservices_def))
    group_newservices_def = SupItemGroup.by_group_name(group_newservices_def)
    
    # hosts groups
    try:
        for name in hostsGroups.keys():
            name = unicode(name)
            hg = SupItemGroup.by_group_name(name)
            if not hg:
                hg = SupItemGroup.create(name=name)
            DBSession.add(hg)
        DBSession.flush()
    except:
        raise
    
    # hosts
    
    # updater: gestion des entités à supprimer
    host_updater = DBUpdater(Host, "name")
    host_updater.load_instances()
    
    lls_updater = DBUpdater2(LowLevelService, "get_key")
    lls_updater.load_instances()
    
    pds_updater = DBUpdater2(PerfDataSource, "get_key")
    pds_updater.load_instances()
    
    for hostname, host in hostsConf.iteritems():
        hostname = unicode(hostname)
        h = Host.by_host_name(hostname)
        # on marque cet host "en conf"
        host_updater.in_conf(hostname)
        
        if h:
            # update host object
            h.checkhostcmd = unicode(host['checkHostCMD'])
            h.hosttpl = unicode(host['hostTPL'])
            h.snmpcommunity = unicode(host['community'])
            h.snmpoidsperpdu = unicode(host['snmpOIDsPerPDU'])
            h.snmpversion = unicode(host['snmpVersion'])
            h.mainip = unicode(host['mainIP'])
            h.snmpport = unicode(host['port'])
            # add groups to host
            h.groups = [SupItemGroup.by_group_name(unicode(host['serverGroup'])), ]
        else:
            # create host object
            h = Host(name=unicode(hostname),
                     checkhostcmd=unicode(host['checkHostCMD']),
                     hosttpl=unicode(host['hostTPL']),
                    snmpcommunity=unicode(host['community']),
                    mainip=unicode(host['mainIP']),
                    snmpport=unicode(host['port']),
                    snmpoidsperpdu=unicode(host['snmpOIDsPerPDU']),
                    weight=1,
                    snmpversion=unicode(host['snmpVersion']))
            DBSession.add(h)
            h.groups = [group_newhosts_def, ]
        
        # low level services
        # TODO: implémenter les détails: op_dep, weight, command
        
        for service in host['services'].keys():
            service = unicode(service)
            lls = LowLevelService.by_host_service_name(hostname, service)
            if not lls:
                lls = LowLevelService(host=h, servicename=service,
                                      op_dep=u'+', weight=1)
                lls.groups = [group_newservices_def, ]
                DBSession.add(lls)
            
            lls_updater.in_conf(lls.get_key())
            
            # nagios generic directives for services
            if host['nagiosSrvDirs'].has_key(service):
                for name, value in host['nagiosSrvDirs'][service].iteritems():
                    name = unicode(name)
                    value = unicode(value)
                    ci = ConfItem.by_host_service_confitem_name(hostname, service, name)
                    if ci:
                        ci.value = value
                    else:
                        ci = ConfItem(supitem=lls, name=name, value=value)
                        DBSession.add(ci)
        
        # nagios generic directives for host
        for name, value in host['nagiosDirectives'].iteritems():
            name = unicode(name)
            value = unicode(value)
            ci = ConfItem.by_host_confitem_name(hostname, name)
            if ci:
                ci.value = value
            else:
                ci = ConfItem(supitem=h, name=name, value=value)
                DBSession.add(ci)
        
        
        for og in host['otherGroups']:
            h.groups.append(SupItemGroup.by_group_name(unicode(og)))
        
        # export graphes groups
        _export_host_graphgroups(host['graphGroups'], h)
        
        # export graphes
        _export_host_graphitems(host['graphItems'], h, pds_updater)
        
    DBSession.flush()
    
    # suppression des hosts qui ne sont plus en conf
    host_updater.update()
    # suppression des lowlevelservices qui ne sont plus en conf
    lls_updater.update()
    # suppression des perfdatasources qui ne sont plus en conf
    pds_updater.update()
    
    # high level services
    hlserviceloader.load_dir(os.path.join(confdir, 'hlservices'), delete_all=True)
    
    # dépendances
    dependencyloader.reset_change()
    dependencyloader.load_dir(os.path.join(confdir, 'dependencies'), delete_all=True)
    dependencyloader.detect_change()
    
    # on détruit les groupes spéciaux
    DBSession.delete(group_newhosts_def)
    DBSession.delete(group_newservices_def)
    DBSession.flush()

def _export_host_graphgroups(graphgroups, h):
    """
    Update database with graphes and graph groups for a host.
    
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
        groupname = unicode(groupname)
        group = GraphGroup.by_group_name(groupname)
        if group:
            group.remove_children() # redundant with graph.groups = [] ?
        else:
            group = GraphGroup.create(name=groupname)
            DBSession.add(group)
        for name in graphnames:
            name = unicode(name)
            graph = DBSession.query(Graph).filter(Graph.name == name).first()
            if not graph:
                graph = Graph(name=name, template=u'lines', vlabel=u'unknown')
            graph.groups.append(group)
    
    DBSession.flush()
        


def _export_host_graphitems(graphitems, h, dbupdater):
    """
    Update database with graph items for a host.
    
    TODO: lien avec host ?
    
    @param graphitems: a dict describing the graph items for a host.
    @type graphitems: C{dict}
    @param h: host
    @param h: C{Host}
    @param dbupdater: gestionnaire de mise à jour pour les perfdatasources
    @param dbupdater: L{DBUpdater}
    @returns: None
    """
    for name, graph in graphitems.iteritems():
        #print name, graph
        name = unicode(name)
        g = DBSession.query(Graph).filter(Graph.name == name).first()
        g.template = graph['template']
        g.vlabel = graph['vlabel']
        
        # création PerfDataSources
        
        for ds in graph['ds']:
            pds = PerfDataSource.by_host_and_source_name(h, ds)
            if not pds:
                pds = PerfDataSource(host=h, name=ds, label=graph['vlabel'])
                pds.graphs = [g,]
            
            dbupdater.in_conf(pds.get_key())
            
            if graph['factors'].has_key(ds):
                pds.factor = float(graph['factors'][ds])
            DBSession.add(pds)
    
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
            vigiloserver = VigiloServer.by_vigiloserver_name(unicode(server))
            
            if not vigiloserver:
                vigiloserver = VigiloServer(name=unicode(server))
                DBSession.add(vigiloserver)
            
            v = Ventilation(host=Host.by_host_name(unicode(host)),
                        vigiloserver=vigiloserver,
                        application=Application.by_app_name(unicode(app)))
            
            DBSession.add(v)
    DBSession.flush()

