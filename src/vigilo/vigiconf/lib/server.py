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
"""
Describes a Server to push and commit new software configurations to
"""

import shutil, os
import syslog
import socket

import conf
from lib import ConfMgrError, EditionError
from lib.systemcommand import SystemCommand, SystemCommandError
from lib.revisionmanager import RevisionManager


class ServerError(ConfMgrError):
    """Exception involving a L{Server} object"""

    def __init__(self, value, iServerName = ''):
        ConfMgrError.__init__(self, value)
        self.value = value
        self.mServer = iServerName

    def __str__(self):
        _srvStr = ""
        if( len(self.mServer)>0):
            _srvStr = " on server %s" % (self.mServer)
        return repr("ServerError : %s%s" % (self.value, _srvStr))


class ServerFactory(object):
    """The Server Factory: returns the right subclass"""

    def __init__(self):
        pass

    def makeServer(self, name):
        """
        Returns the right server object, depending on the hostname
        @param name: the hostname of the Server object to create
        @type  name: C{str}
        @returns: Server object with the provided hostname
        @rtype: L{Server}
        """
        localnames = [ "localhost", socket.gethostname(), socket.getfqdn() ]
        if name in localnames:
            from lib.servertypes.local import ServerLocal
            return ServerLocal(name)
        else:
            try:
                from lib.servertypes.remote import ServerRemote
            except ImportError:
                raise EditionError("On the Community Edition, you can only "
                                  +"use the localhost", name)
            return ServerRemote(name)


class Server(object):
    """
    A generic Server class
    @ivar mName: the hostname
    @type mName: C{str}
    @ivar mRevisionManager: the revision manager
    @type mRevisionManager: L{RevisionManager
        <lib.revisionmanager.RevisionManager>}
    """

    def __init__(self, iName):
        self.mName = iName
        # mRevisionManager
        self.mRevisionManager = RevisionManager()
        self.mRevisionManager.setRepository(conf.svnRepository)
        self.mRevisionManager.setFilename(os.path.join(
                conf.libDir, "revisions" , iName + ".revisions"))

    def getName(self):
        """@return: L{mName}"""
        return self.mName
    
    def getRevisionManager(self):
        """@return: L{mRevisionManager}"""
        return self.mRevisionManager
    
    def needsDeployment(self):
        """
        Tests wheather the server needs deployment
        @rtype: C{boolean}
        """
        return self.getRevisionManager().isDeployNeeded()
    
    def needsRestart(self):
        """
        Tests wheather the server needs restarting
        @rtype: C{boolean}
        """
        return self.getRevisionManager().isRestartNeeded()
    
    # external references
    def getBaseDir(self):
        """
        @return: base directory for file deployment
        @rtype: C{str}
        """
        return os.path.join(conf.libDir, "deploy")
    
    def createCommand(self, iCommand):
        """
        @note: To be implemented by subclasses
        @param iCommand: command to execute
        @type  iCommand: C{str}
        @return: the command instance
        @rtype: L{SystemCommand<lib.systemcommand.SystemCommand>}
        """
        c = SystemCommand(iCommand)
        c.simulate = getattr(conf, "simulate", False)
        return c

    # methods
    def switchDirectories(self):
        """
        Archive the directory containing the config files
    
        All the following commands must success or the whole command fails:
         1. test if the DIRECTORY "/tmp/testMV/new" exists
         2. cd into /tmp/testMV
         3. if the DIRECTORY prod exists, rename it to old
         4. rename new to prod
        """
        _CmdLine = "[ -d %(base)s/new ] && " \
                 +"( [ -d %(base)s/prod ] || mkdir %(base)s/prod ) && " \
                 +"rm -rf %(base)s/old && mv %(base)s/prod %(base)s/old && " \
                 +"mv %(base)s/new %(base)s/prod && mkdir %(base)s/new && " \
                 +"cp -f %(base)s/prod/revisions.txt %(base)s/new/revisions.txt"
        # Wrap in sudo, and quote it
        _CmdLine = "sudo sh -c '"+_CmdLine+"'"
        # execution
        _command = self.createCommand( _CmdLine %
                                    {"base": conf.baseConfDir} )
        try:
            _command.execute()
        except SystemCommandError, e:
            raise ServerError("Can't refactor server. COMMAND %s FAILED. "
                              % _CmdLine + "REASON : %s" % e.value,
                              self.getName())
 
    def _builddepcmd(self):
        """
        Build the deployment command line
        @note: To be implemented by subclasses.
        """
        return ""

    def deployFiles(self):
        """
        Copy all the configuration files
        """
        _commandline = self._builddepcmd()
        _command = SystemCommand(_commandline)
        # Simulation mode ?
        _command.simulate = getattr(conf, "simulate", False)
        try:
            _command.execute()
        except SystemCommandError, e:
            raise ServerError("Can't deploy server. REASON : %s" % (e.value),
                              self.getName())
        syslog.syslog(syslog.LOG_INFO, "%s : deployement successful." \
                                       % (self.getName()))

    def copy(self, iDestination, iSource):
        """
        Simple wrapper around shutil.copyfile.
        @param iDestination: destination
        @type  iDestination: C{str}
        @param iSource: source
        @type  iSource: C{str}
        @todo: reverse arguments order
        """
        try:
            shutil.copyfile(iSource, iDestination)
        except Exception, e:
            raise ServerError("Can not copy files (%s to %s): %s. "
                              % (iSource, iDestination, e), self.getName())

    def insertValidationDir(self):
        """Prepare the directory with the validation scripts"""
        try:
            _commandStr = "mkdir %s/%s/validation && " \
                          % (self.getBaseDir(), self.getName()) \
                         +"cp %s/validation/*.sh %s/%s/validation/" \
                          % (conf.dataDir, self.getBaseDir(), self.getName())
            # instanciates a new systemcommand
            _command = SystemCommand(_commandStr)
            _command.execute()
        except SystemCommandError, e:
            raise ServerError("Can not insert 'validation' directory in "
                             +"configuration: %s." % e, self.getName())
        
    def deploy(self, iRevision):
        """Do the deployment"""
        # update local revision files
        self.getRevisionManager().setSubversion(iRevision)
        self.getRevisionManager().setDeployed(iRevision)
        self.getRevisionManager().writeConfigFile()
        # copy the revisionfile to the deployment directory
        self.copy("%s/%s/revisions.txt" % (self.getBaseDir(), self.getName()),
                  self.getRevisionManager().getFilename())
        # insert the "validation" directory in the deployment directory
        self.insertValidationDir()
        # now, the deployment directory is complete.
        self.deployFiles()
 
    def undo(self):
        """Undo a deployment"""
        # check if the directory exists
        try:
            _CmdLine = "sh -c '[ -d %s/old ] && [ -d %s/new ]'" \
                       % (conf.baseConfDir, conf.baseConfDir)
             # execution
            _command = self.createCommand(_CmdLine)
            _command.execute()
            if(_command.integerReturnCode() == 1):
                raise ServerError("UNDO can't be done. Directory 'old' "
                                 +"does not exist on %s." % self.getName(),
                                  self.getName())
        except SystemCommandError, e:
            raise ServerError("UNDO can't be done. %s" % (str(e)),
                              self.getName())
        # undo !
        try:
            
            _newundoStr = "mv %s/new %s/undo" \
                          % (conf.baseConfDir, conf.baseConfDir)
            _oldnew = "mv %s/old %s/new" \
                      % (conf.baseConfDir, conf.baseConfDir)
            _undoold = "mv %s/undo %s/old" \
                       % (conf.baseConfDir, conf.baseConfDir)
            
            _CmdLine = "sudo sh -c ' %s && %s && %s '" \
                       % (_newundoStr, _oldnew, _undoold)
             # execution
            _command = self.createCommand(_CmdLine)
            _command.execute()
            if(_command.integerReturnCode() == 1):
                raise ServerError("UNDO failed on %s." \
                                  % (self.getName()), self.getName())
            else:
                syslog.syslog(syslog.LOG_INFO,
                              "UNDO done on %s." % (self.getName()))
        except SystemCommandError, e:
            raise ServerError("UNDO can't be done. %s" % (str(e)),
                              self.getName())

    # redirections
    def getDeployed(self):
        """
        @return: The deployed SVN revision from the
            L{RevisionManager<lib.revisionmanager.RevisionManager>}
        """
        return self.getRevisionManager().getDeployed()

    def getInstalled(self):
        """
        @return: The installed SVN revision from the
            L{RevisionManager<lib.revisionmanager.RevisionManager>}
        """
        return self.getRevisionManager().getInstalled()

    def getPrevious(self):
        """
        @return: The previous SVN revision from the
            L{RevisionManager<lib.revisionmanager.RevisionManager>}
        """
        return self.getRevisionManager().getPrevious()
    
    def updateRevisionManager(self):
        """
        Update the SVN revisions in the
        L{RevisionManager<lib.revisionmanager.RevisionManager>}
        """
        self.getRevisionManager().update(self)    


# vim:set expandtab tabstop=4 shiftwidth=4:
