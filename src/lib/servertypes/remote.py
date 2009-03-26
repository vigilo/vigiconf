################################################################################
#
# Copyright (C) 2007-2009 CS-SI
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

import os

import conf
from lib.server import Server, ServerError
from lib.systemcommand import SystemCommand
from lib.remotecommand import RemoteCommand, CommandUser

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
        ssh_conf_file = os.path.join(conf.libDir, "db", "ssh_config")
        if not os.path.exists(ssh_conf_file):
            raise ServerError("Cannot find SSH config file: %s"
                                        % ssh_conf_file)
        self.mCommandUser = CommandUser("confmgr",
                os.path.join(conf.libDir, "db", "ssh_config"))

        
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
        @rtype: L{SystemCommand<lib.systemcommand.SystemCommand>}
        """
        c = RemoteCommand(self.getName(), iCommand, self.getCommandUser())
        c.simulate = getattr(conf, "simulate", False)
        return c

    def _builddepcmd(self):
        """
        Build the deployment command line
        """
        # Archive the directory containing the config files.
        # The output is the standard output
        _localCommandStr = "tar -C %s/%s -cf - . " % \
                           (self.getBaseDir(), self.getName())
        _remoteCommandStr = "\"cd %s && " % conf.baseConfDir \
                           +"sudo rm -rf new && " \
                           +"sudo mkdir new && cd new && " \
                           +"sudo tar xf - && " \
                           +"sudo chmod -R o-w *\""
        
        _localCommand = SystemCommand(_localCommandStr)
        
        _remoteCommand = self.createCommand(_remoteCommandStr)
        _commandline = _localCommand.getCommand() + " | " \
                      +_remoteCommand.getCommand()
        return _commandline
        

# vim:set expandtab tabstop=4 shiftwidth=4:
