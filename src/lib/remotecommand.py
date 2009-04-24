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
This module wraps SSH commands to copy files, launch remote commands.

This file is part of the Enterprise Edition
"""

import re
import doctest

from lib.systemcommand import SystemCommand, SystemCommandError


class CommandUser(object):
    """
    A user that will execute a command
    @ivar mName: username
    @type mName: C{str}
    @ivar mConfigurationPath: path to the ssh config file.
    @type mConfigurationPath: C{str}
    """

    def __init__(self, iUserName='', iConfigPath=''):
        self.mName = iUserName
        self.mConfigurationPath = iConfigPath
    
    def getName(self):
        """
        @return: L{mName}
        @rtype: C{str}
        """
        return self.mName
    
    def getConfigurationPath(self):
        """
        @return: L{mConfigurationPath}
        @rtype: C{str}
        """
        return self.mConfigurationPath
    
    def __str__(self):
        """
        @return: string representation of this instance.
        @rtype: C{str}
        """
        return "Command User<%s, %s>" \
               % (self.getName(), self.getConfigurationPath())


class RemoteCommandError(SystemCommandError):
    """Exceptions that will be generated by instances of RemoteCommand"""

    def __str__(self):
        return repr("RemoteCommandError : "+self.value)


class RemoteCommand(SystemCommand):
    """
    Commands that will be executed on a remote server using ssh or scp
    @ivar iServer: The remote server that will execute a command
    @type iServer: C{str}
    @ivar iBaseCommand: The command to be executed (optional)
    @type iBaseCommand: C{str}
    @ivar iUser: The user that will execute the command (optional)
    @type iUser: L{CommandUser<lib.remotecommand.CommandUser>}
    """

    def __init__(self, iServer, iBaseCommand='', iUser=None, simulate=False):
        """
        Constructor, sets L{iServer}, L{iBaseCommand}, and L{iUser}.
        @param iServer: the remote server that will execute a command
        @type iServer: C{str}
        @param iBaseCommand: the command to be executed (optional)
        @type iBaseCommand: C{str}
        @param iUser: the user that will execute the command (optional)
        @type iUser: L{CommandUser<lib.remotecommand.CommandUser>}
        @param simulate: if True, do not actually execute the command
        @type  simulate: boolean
        """
        # private attributes
        self.mCommandType = ''
        self.mDestinationStr = ''
        self.mSourceStr = ''
        SystemCommand.__init__(self, iBaseCommand=iBaseCommand,
                                     simulate=simulate)
        # public
        self.setUser(iUser)
        self.setServer(iServer) # mandatory
        
    def setServer(self, iServer):
        """
        Sets the L{iServer} instance variable
        @param iServer: the remote server that will execute a command
        @type iServer: C{str}
        """
        if iServer is None:
            raise RemoteCommandError("Server name set to None.")
        if len(iServer) == 0:
            raise RemoteCommandError("Server name incorrect (length = 0).")
        self.mServer = iServer # pylint: disable-msg=W0201
            
    def setUser(self, iUser):
        """
        Sets the L{iUser} instance variable
        @param iUser: the user that will execute the command (optional)
        @type iUser: L{CommandUser<lib.remotecommand.CommandUser>}
        """
        if(iUser == None):
            iUser = CommandUser()
        self.mUser = iUser # pylint: disable-msg=W0201
    
    def getServer(self):
        """
        @return: L{iServer}
        @rtype: C{str}
        """
        return self.mServer # pylint: disable-msg=W0201
        
    def getUser(self):
        """
        @return: L{iUser}
        @rtype: L{CommandUser<lib.remotecommand.CommandUser>}
        """
        return self.mUser # pylint: disable-msg=W0201
    
    def setCommand(self, iCommand):
        """
        Builds the ssh command from the iCommand provided
        @param iCommand: Command to execute remotely
        @type  iCommand: C{str}
        """
        self.mCommand = iCommand
        self.mCommandType = 'shell'
        
    def getCommand(self):
        """
        @return: Full SSH/SCP wrapped command
        @rtype: C{str}
        """
        if self.mCommandType == 'shell':
            return "ssh -o BatchMode=yes %s %s \"%s\"" \
                   % (self.getConfigurationString(),
                      self.getServerString(),
                      self.mCommand)
        elif self.mCommandType == 'copyTo':
            return "scp -o BatchMode=yes %s %s %s:%s" \
                   % (self.getConfigurationString(),
                      self.mSourceStr,
                      self.getServerString(),
                      self.mDestinationStr)
        elif self.mCommandType == 'copyFrom':
            return "scp -o BatchMode=yes %s %s:%s %s" \
                   % (self.getConfigurationString(),
                      self.getServerString(),
                      self.mSourceStr,
                      self.mDestinationStr)
        else:
            raise RemoteCommandError('Unknown command type.')
        

    def asCopyTo(self, iDestinationPath, iSourcePath):
        """
        Builds a "scp" command to copy a local file to a remote server
        @param iDestinationPath: destination path on the remote server
        @type iDestinationPath: C{str}
        @param iSourcePath: source path on the local server
        @type iSourcePath: C{str}
        """
        self.mDestinationStr = iDestinationPath
        self.mSourceStr = iSourcePath
        self.mCommandType = 'copyTo'
        
    def copyTo(self, iDestinationPath, iSourcePath):
        """
        Executes a "scp" command to copy a local file to a remote server
        @param iDestinationPath: destination path on the remote server
        @type iDestinationPath: C{str}
        @param iSourcePath: source path on the local server
        @type iSourcePath: C{str}
        """
        try:
            self.asCopyTo(iDestinationPath, iSourcePath)
            self.execute()
        except SystemCommandError, sce:
            if re.search("ssh:.*Name or service not known",
                         sce.value) != None:
                raise RemoteCommandError('Cannot reach server.')
            elif re.search("scp:.*No such file or directory",
                           sce.value) != None:
                raise RemoteCommandError('Cannot find file.')
            else:
                raise sce.value
        
    def asCopyFrom(self, iDestinationPath, iSourcePath):
        """
        Builds a "scp" command to copy a remote file to the local machine
        @param iDestinationPath: destination path on the local server
        @type iDestinationPath: C{str}
        @param iSourcePath: source path on the remote server
        @type iSourcePath: C{str}
        """
        self.mDestinationStr = iDestinationPath
        self.mSourceStr = iSourcePath
        self.mCommandType = 'copyFrom'
    
    def copyFrom(self, iDestinationPath, iSourcePath):
        """
        Executes a "scp" command to copy a remote file to the local machine
        @param iDestinationPath: destination path on the local server
        @type iDestinationPath: C{str}
        @param iSourcePath: source path on the remote server
        @type iSourcePath: C{str}
        """
        try:
            self.asCopyFrom(iDestinationPath, iSourcePath)
            self.execute()
        except SystemCommandError, e:
            if re.search("ssh:.*Name or service not known", e.value) != None:
                raise RemoteCommandError('Cannot reach server.')
            elif re.search("scp:.*No such file or directory", e.value) != None:
                raise RemoteCommandError('Cannot find file.')
            else:
                raise e.value
        
    def getConfigurationString(self):
        """
        @returns: The SSH option to set the path to the SSH config file
        @rtype: C{str}
        """
        _confpath = self.getUser().getConfigurationPath()
        if(len(_confpath)>0):
            return "-F %s" % (_confpath)
        return "" # else
    
    def getServerString(self):
        """
        @returns: The complete user@server string (if any)
        @rtype: C{str}
        """
        if(len(self.getUser().getName())>0):
            return "%s@%s" % (self.getUser().getName(), self.getServer())
        else:
            return "%s" % (self.getServer())


if __name__ == "__main__":
    doctest.testfile("remotecommand_unittest.txt")    


# vim:set expandtab tabstop=4 shiftwidth=4:
