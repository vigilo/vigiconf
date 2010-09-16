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

from ..server import Server, ServerError
from ..systemcommand import SystemCommand, SystemCommandError
from ..remotecommand import RemoteCommand, CommandUser

from vigilo.common.gettext import translate
_ = translate(__name__)

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
                                     "ssh", "ssh_config")
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

    def createCommand(self, iCommand, shell=False):
        """
        @param iCommand: command to execute
        @type  iCommand: C{str}
        @return: the command instance
        @rtype: L{SystemCommand<lib.systemcommand.SystemCommand>}
        """
        c = RemoteCommand(self.getName(), iCommand,
                          self.getCommandUser(), shell=shell)
        c.simulate = self.is_simulation()
        return c

    def deployTar(self):
        self.remoteCopyTar()
        self.remoteDeployTar()

    def remoteCopyTar(self):
        cmd = RemoteCommand(self.getName())
        tar_src = os.path.join(self.getBaseDir(), "%s.tar" % self.getName())
        tar_dest = os.path.join(settings["vigiconf"].get("targetconfdir"),
                                "tmp", "vigiconf.tar")
        try:
            cmd.copyTo(tar_dest, tar_src)
        except SystemCommandError, e:
            raise ServerError(_("Can't copy the config. archive to %s: %s")
                                % (self.getName(), e.value))
        finally:
            os.remove(tar_src)

    def remoteDeployTar(self):
        tar_dest = os.path.join(settings["vigiconf"].get("targetconfdir"),
                                "tmp", "vigiconf.tar")
        cmd = self.createCommand(["vigiconf-local", "receive-conf", tar_dest])
        try:
            cmd.execute()
        except SystemCommandError, e:
            raise ServerError(_("Can't deploy the config. for server %s: %s")
                               % (self.getName(), e.value))


# vim:set expandtab tabstop=4 shiftwidth=4:
