# -*- coding: utf-8 -*-
################################################################################
#
# Copyright (C) 2007-2010 CS-SI
#
# This program is free software; you can redistribute it and/or modify
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
Describes a Server where to push and commit new software configurations

This file is part of the Enterprise Edition
"""

from __future__ import absolute_import

import os

from vigilo.common.conf import settings
from vigilo.models import tables
from vigilo.models.session import DBSession

from vigilo.vigiconf import conf
from .base import Server, ServerError
from .manager import ServerManager
from vigilo.vigiconf.lib.exceptions import VigiConfError
from vigilo.vigiconf.lib.systemcommand import SystemCommandError
from vigilo.vigiconf.lib.remotecommand import RemoteCommand, CommandUser
from vigilo.vigiconf.lib.remotecommand import RemoteCommandError

from vigilo.common.gettext import translate
_ = translate(__name__)


class ServerManagerRemote(ServerManager):

    def list(self):
        """
        Get all server names from configuration
        @return: the servers names from the configuration.
        @rtype: C{set} of C{str}
        """
        _serversList = set()
        for appGroup in conf.appsGroupsByServer:
            for hostGroup in conf.appsGroupsByServer[appGroup]:
                for server in conf.appsGroupsByServer[appGroup][hostGroup]:
                    _serversList.add(server)
        for appGroup in getattr(conf, "appsGroupsBackup", {}):
            for hostGroup in conf.appsGroupsBackup[appGroup]:
                for server in conf.appsGroupsBackup[appGroup][hostGroup]:
                    _serversList.add(server)
        self.servers = dict([ (s, self.factory.makeServer(s))
                              for s in _serversList ])

    def restrict(self, servernames):
        """
        @param servernames: List of servers to filter from
        @type  servernames: C{list} of C{str}
        @return: Intersection between servers and self.L{servers}
        @rtype:  C{list} of C{str}
        """
        if not servernames:
            return
        # vérification de la liste en argument
        for servername in servernames:
            if servername not in self.servers:
                message = _("Invalid server name: %(servername)s. "
                            "Available servers: %(servers)s") \
                            % {"servername": servername,
                               "servers": ", ".join(self.servers)}
                raise KeyError(message)
        # filtrage de la liste
        for servername in self.servers.keys():
            if servername not in servernames:
                del self.servers[servername]


class ServerRemote(Server):
    """
    A SSH-accessible server
    @ivar mCommandUser: the user to execute the command as
    @type mCommandUser: L{CommandUser<lib.remotecommand.CommandUser>}
    """

    def __init__(self, iName):
        # Superclass constructor
        Server.__init__(self, iName)
        # mCommandUser
        ssh_conf_file = os.path.join(settings["vigiconf"].get("confdir"),
                                     "..", "ssh", "ssh_config")
        if not os.path.exists(ssh_conf_file):
            raise ServerError(_("Cannot find SSH config file: %s")
                                        % ssh_conf_file)
        self.mCommandUser = CommandUser("vigiconf", ssh_conf_file)


    def setCommandUser(self, iUser):
        """
        Sets L{mCommandUser}
        @param iUser: the user instance
        @type  iUser: L{CommandUser<lib.remotecommand.CommandUser>}
        """
        self.mCommandUser = iUser

    def getCommandUser(self):
        """@return: L{mCommandUser}"""
        return self.mCommandUser

    def createCommand(self, iCommand):
        """
        @param iCommand: command to execute
        @type  iCommand: C{str}
        @return: the command instance
        @rtype: L{SystemCommand<vigilo.vigiconf.lib.systemcommand.SystemCommand>}
        """
        c = RemoteCommand(self.getName(), iCommand, self.getCommandUser())
        c.simulate = self.is_simulation()
        return c

    def deployTar(self):
        self.remoteCopyTar()
        self.remoteDeployTar()

    def remoteCopyTar(self):
        tar_src = os.path.join(self.getBaseDir(), "%s.tar" % self.getName())
        tar_dest = os.path.join(settings["vigiconf"].get("targetconfdir"),
                                "tmp", "vigiconf.tar")
        if not os.path.exists(tar_src):
            raise RemoteCommandError(None,
                        _("The archive file does not exist: %s") % tar_src)
        cmd = self.createCommand(None)
        try:
            cmd.copyTo(tar_dest, tar_src)
        except SystemCommandError, e:
            raise ServerError(_("Can't copy the configuration archive "
                                "to %(server)s: %(error)s") % {
                                    'server': self.getName(),
                                    'error': e.value,
                                })
        finally:
            os.remove(tar_src)

    def remoteDeployTar(self):
        tar_dest = os.path.join(settings["vigiconf"].get("targetconfdir"),
                                "tmp", "vigiconf.tar")
        cmd = self.createCommand(["vigiconf-local", "receive-conf", tar_dest])
        try:
            cmd.execute()
        except SystemCommandError, e:
            raise ServerError(_("Can't deploy the configuration for "
                                "server %(server)s: %(error)s") % {
                                    'server': self.getName(),
                                    'error': e.value,
                                })

    def is_enabled(self):
        """@see: L{lib.dispatchator.Dispatchator.filter_disabled}"""
        server_db = tables.VigiloServer.by_vigiloserver_name(
                            unicode(self.name))
        if server_db is None:
            # pas en base, donc pas désactivé (peut-être qu'il vient
            # d'être ajouté)
            return True
        if server_db.disabled:
            return False
        else:
            return True

    def disable(self):
        """
        Désactive ce serveur Vigilo
        """
        vserver = tables.VigiloServer.by_vigiloserver_name(unicode(self.name))
        if vserver is None:
            raise VigiConfError(_("The Vigilo server %s does not exist")
                                % self.name)
        if vserver.disabled:
            raise VigiConfError(_("The Vigilo server %s is already disabled")
                                % self.name)
        vserver.disabled = True
        DBSession.flush()

    def enable(self):
        """
        Active ce serveur Vigilo
        """
        vserver = tables.VigiloServer.by_vigiloserver_name(unicode(self.name))
        if vserver is None:
            raise VigiConfError(_("The Vigilo server %s does not exist")
                                % self.name)
        if not vserver.disabled:
            raise VigiConfError(_("The Vigilo server %s is already enabled")
                                % self.name)
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


# vim:set expandtab tabstop=4 shiftwidth=4:
