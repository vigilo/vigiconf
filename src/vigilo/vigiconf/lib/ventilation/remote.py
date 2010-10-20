# -*- coding: utf-8 -*-
################################################################################
#
# VigiConf
# Copyright (C) 2007-2011 CS-SI
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

# pylint: disable-msg=E1101

"""
Module in charge of finding the good server to handle a given application
for a given host defined in the configuration.

This file is part of the Enterprise Edition
"""

from __future__ import absolute_import

import transaction

from vigilo.models.session import DBSession
from vigilo.models import tables

from vigilo.common.conf import settings
from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib import ParsingError, VigiConfError
from vigilo.vigiconf.lib.ventilation import Ventilator


__docformat__ = "epytext"
__all__ = ("VentilatorRemote",)


class VentilatorRemote(Ventilator):

    def __init__(self, apps):
        super(VentilatorRemote, self).__init__(apps)
        self.apps_by_appgroup = self.get_app_by_appgroup()

    def appendHost(self, vservername, hostname, appgroup):
        """
        Append a host to the database
        @param vservername: Vigilo server name
        @type  vservername: C{str}
        @param hostname: the host to append
        @type  hostname: C{str}
        """
        vserver = tables.VigiloServer.by_vigiloserver_name(unicode(vservername))
        host = tables.Host.by_host_name(unicode(hostname))
        for app in self.apps_by_appgroup[appgroup]:
            application = tables.Application.by_app_name(unicode(app.name))
            if not application:
                raise VigiConfError(_("Can't find application %s in database")
                                    % app.name)
            DBSession.add(tables.Ventilation(
                                vigiloserver=vserver,
                                host=host,
                                application=application,
                          ))
        DBSession.flush()


    def getNextServerToUse(self, servers):
        """
        @param servers: the list of server names
        @type servers: list of C{str}
        @return: the less busy server's name
        """
        loads = {}
        for server in servers:
            # TODO: optimisation : préparer la requête
            loads[server] = DBSession.query(tables.Ventilation).join(
                                    tables.Ventilation.vigiloserver
                                ).filter(
                                    tables.VigiloServer.name == unicode(server)
                                ).count()
        servers.sort(key=lambda s: loads[s])
        return servers[0]

    def get_previous_server(self, host, appgroup):
        for app in self.apps_by_appgroup[appgroup]:
            prev_srv = DBSession.query(tables.VigiloServer.name
                            ).join(tables.Ventilation.vigiloserver
                            ).join(tables.Ventilation.application
                            ).filter(
                                tables.Application.name == unicode(app.name)
                            ).join(tables.Ventilation.host
                            ).filter(
                                tables.Host.name == unicode(host)
                            ).filter(
                                tables.VigiloServer.disabled == False
                            ).first()
            if prev_srv is not None:
                return prev_srv.name
        return None

    def getServerToUse(self, servers, host, appgroup):
        """
        Find the server to use for a given host.
        If the host is already handled by a server, return it.
        Choose the less busy otherwise.
        @param servers: the list of server names
        @type  servers: list of C{str}
        @param host: the host name to handle
        @type  host: C{str}
        @param appgroup: the application group to ventilate
        @type  appgroup: C{str}
        @return: the server to use
        @rtype:  C{str}
        """
        previous_server = self.get_previous_server(host, appgroup)
        if previous_server and previous_server in servers:
            return previous_server
        # not found yet, choose next server
        vserver = self.getNextServerToUse(servers)
        self.appendHost(vserver, host, appgroup)
        return vserver

    def is_mode_duplicate(self, appgroup, hostgroup):
        if getattr(conf, "appsGroupsMode", None) is None:
            return False
        if appgroup not in conf.appsGroupsMode:
            return False
        if hostgroup not in conf.appsGroupsMode[appgroup]:
            return False
        return conf.appsGroupsMode[appgroup][hostgroup] == "duplicate"

    def get_host_ventilation_group(self, hostname, hostdata):
        if "serverGroup" in hostdata and hostdata["serverGroup"]:
            return hostdata["serverGroup"]
        groups = set()
        host = tables.Host.by_host_name(unicode(hostname))
        if not host:
            raise KeyError("Trying to ventilate host %s, but it's not in the "
                           "database yet" % hostname)
        for group in host.groups:
            groups.add(group.get_top_parent().name)

        if not groups:
            raise ParsingError('Could not determine how to '
                'ventilate host "%s". Affect some groups to '
                'this host or use the ventilation attribute.' %
                hostname)

        if len(groups) != 1:
            raise ParsingError('Found multiple candidates for '
                'ventilation (%(candidates)r) on "%(host)s", '
                'use the ventilation attribute to select one.' % {
                    'candidates': ', '.join(map(str, groups)),
                    'host': hostname,
                })
        ventilation = groups.pop()
        hostdata['serverGroup'] = ventilation
        return ventilation

    def get_app_by_appgroup(self):
        appgroups = {}
        for app in self.apps:
            appgroups.setdefault(app.group, []).append(app)
        return appgroups

    def filter_vservers(self, vserverlist):
        """
        Filtre une liste pour ne garder que les serveurs qui ne sont pas désactivés.
        Désactive un serveur Vigilo
        @param vservername: nom du serveur Vigilo
        @type  vservername: C{str}
        """
        for vservername in vserverlist:
            vserver = tables.VigiloServer.by_vigiloserver_name(unicode(vservername))
            if vserver is None:
                raise VigiConfError(_("The Vigilo server %s does not exist")
                                    % vservername)
            if vserver.disabled:
                vserverlist.remove(vservername)
        return vserverlist

    def ventilate(self):
        """
        Try to find the best server where to monitor the hosts contained in the
        I{conf}.

        @return: a dict of the ventilation result. The dict content is:
          - B{Key}: name of a host
          - B{value}: a dict in the form:
            - B{Key}: the name of an application for which we have to deploy a
              configuration for this host
              (Nagios, CorrSup, Collector...)
            - B{Value}: the hostname of the server where to deploy the conf for
              this host and this application

        I{Example}:

          >>> ventilate()
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
        LOGGER.debug("Ventilation")
        r = {}
        for (host, v) in conf.hostsConf.iteritems():
            hostGroup = self.get_host_ventilation_group(host, v)
            app_to_vservers = {}
            for appGroup in conf.appsGroupsByServer:
                if appGroup not in self.apps_by_appgroup \
                        or not self.apps_by_appgroup[appGroup]:
                    continue # pas d'appli dans ce groupe
                vservers = conf.appsGroupsByServer[appGroup][hostGroup]
                vservers = self.filter_vservers(vservers)
                if not vservers:
                    continue # pas de serveurs affectés à ce groupe
                if len(vservers) == 1:
                    servers = [vservers[0], ]
                elif self.is_mode_duplicate(appGroup, hostGroup):
                    servers = vservers
                else:
                    # choose wisely
                    servers = self.getServerToUse(vservers, host, appGroup)
                    servers = [servers, ]
                for app in self.apps_by_appgroup[appGroup]:
                    app_to_vservers[app] = servers
            r[host] = app_to_vservers
        return r

    # Gestion des serveurs Vigilo

    def disable_server(self, vservername):
        """
        Désactive un serveur Vigilo
        @param vservername: nom du serveur Vigilo
        @type  vservername: C{str}
        """
        vserver = tables.VigiloServer.by_vigiloserver_name(unicode(vservername))
        if vserver is None:
            raise VigiConfError(_("The Vigilo server %s does not exist")
                                % vservername)
        if vserver.disabled:
            raise VigiConfError(_("The Vigilo server %s is already disabled")
                                % vservername)
        vserver.disabled = True
        DBSession.flush()
        transaction.commit()

    def enable_server(self, vservername):
        """
        Active un serveur Vigilo
        @param vservername: nom du serveur Vigilo
        @type  vservername: C{str}
        """
        vserver = tables.VigiloServer.by_vigiloserver_name(unicode(vservername))
        if vserver is None:
            raise VigiConfError(_("The Vigilo server %s does not exist")
                                % vservername)
        if not vserver.disabled:
            raise VigiConfError(_("The Vigilo server %s is already enabled")
                                % vservername)
        # On efface les associations précédentes
        prev_ventil = DBSession.query(
                    tables.Ventilation.idapp, tables.Ventilation.idhost
                ).filter(
                    tables.Ventilation.idvigiloserver == vserver.idvigiloserver
                ).all()
        for idapp, idhost in prev_ventil:
            temp_ventils = DBSession.query(tables.Ventilation
                ).filter(
                    tables.Ventilation.idapp == idapp
                ).filter(
                    tables.Ventilation.idhost == idhost
                ).filter(
                    tables.Ventilation.idvigiloserver != vserver.idvigiloserver
                ).all()
            for temp_ventil in temp_ventils:
                DBSession.delete(temp_ventil)
        vserver.disabled = False
        DBSession.flush()
        transaction.commit()


# vim:set expandtab tabstop=4 shiftwidth=4:
