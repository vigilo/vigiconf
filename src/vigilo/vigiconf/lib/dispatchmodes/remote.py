################################################################################
#
# ConfigMgr Data Consistancy dispatchator
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

# pylint: disable-msg=E1101

"""
Remote deployment mode.

This file is part of the Enterprise Edition.
"""

from __future__ import absolute_import

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

from ... import conf
from ...dispatchator import Dispatchator


class DispatchatorRemote(Dispatchator):
    """
    Dispatch the configurations files for all the applications.
    @ivar mAppsList: list of all the applications contained in the configuration
    @type mAppsList: list of strings
    @ivar mServers: servers that will be used for operations
    @type mServers: list of L{Server<lib.server.Server>} objects
    @ivar mApplications: application deployed on mServers
    @type mApplications: list of L{Application<lib.application.Application>}
        objects
    @ivar mModeForce: defines if the --force option is set
    @type mModeForce: C{boolean}
    @ivar mUser: username to do remote operations
    @type mUser: L{CommandUser<lib.remotecommand.CommandUser>}
    """
    def __init__(self):
        Dispatchator.__init__(self)
        self.mUser = None
        # initialize servers
        self.setServers(
                self.buildServersFrom(
                    self.listServerNames()
            ))

    def setUser(self, iUser):
        """
        Mutator on mUser
        @type iUser: L{CommandUser<lib.remotecommand.CommandUser>}
        """
        self.mUser = iUser    

    def listServerNames(self):
        """
        Get all server names from configuration
        @return: the servers names from the configuration.
        @rtype: C{set} of C{str}
        """
        _serversList = set()
        for appGroup in conf.appsGroupsByServer:
            for hostGroup in conf.appsGroupsByServer[appGroup]:
                for server in conf.appsGroupsByServer[appGroup][hostGroup]
                    _serversList.add(server)
        return _serversList

    def getServersForApp(self, app):
        """
        Get the list of server names for this app.
        @param app: the application to consider
        @type  app: L{lib.application.Application}
        @rtype: C{list} of C{str}
        """
        # First, get the app group
        appgroup = app.getGroup()
        # If we're not listed in the appsGroupsByServer matrix, bail out
        if not conf.appsGroupsByServer.has_key(appgroup):
            LOGGER.warning(_("The %s app group is not listed in "
                                "appsGroupsByServer"), appgroup)
            return []
        # Then, find all hostgroups
        hostgroups = set()
        for hostdata in conf.hostsConf.values():
            hostgroups.add(hostdata['serverGroup'])
        servers = list()
        # Now, use the appgroup to hostgroup to server mapping
        for hostgroup in hostgroups:
            if not conf.appsGroupsByServer[appgroup].has_key(hostgroup):
                continue
            servers.extend(conf.appsGroupsByServer[appgroup][hostgroup])
        # uniquify
        servers = list(set(servers))
        return servers

    def restrict(self, servernames):
        """
        Restrict applications and servers to the ones given as argument.
        @param servernames: List of servers to filter from
        @type  servernames: C{list} of C{str}
        """
        if not servernames:
            return
        for servername in servernames:
            if servername not in self.getServersList():
                message = _("Invalid server name: %(servername)s. "
                            "Available servers: %(servers)s") \
                            % {"servername": servername,
                               "servers": ", ".join(self.getServersList())}
                raise KeyError(message)
        self.restrictServersList(servernames)
        self.restrictApplicationsListToServers(servernames)

    def restrictServersList(self, servernames):
        """
        @param servernames: List of servers to filter from
        @type  servernames: C{list} of C{str}
        @return: Intersection between servers and self.L{mServers}
        @rtype:  C{list} of C{str}
        """
        if not servernames:
            return
        newservers = []
        for server in self.getServers():
            if server.getName() in servernames:
                newservers.append(server)
        self.setServers(newservers)

    def restrictApplicationsListToServers(self, servernames):
        """
        Restricts our applications' servers to the servers list
        @param servernames: List of servers to filter from
        @type  servernames: C{list} of C{str}
        """
        newapplications = []
        for _app in self.getAppsList():
            serversforapp = []
            for _srv in _app.getServers():
                if _srv.getName() in servernames: # keep it
                    serversforapp.append(_srv)
            if serversforapp: # if there a no server left, just drop the app
                _app.setServers(serversforapp)
                newapplications.append(_app)
        self.setApplications(newapplications)



# vim:set expandtab tabstop=4 shiftwidth=4:
