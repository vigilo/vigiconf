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

""" Defines an application that is managed by the ConfMgr
  - Nagios
  - StoreMe
  - CorrSup
  - SupNavigator
  - NagVis
  - Apache
  - Bind
  - RRDGraph
  - ...
"""

from __future__ import absolute_import

import syslog
import Queue
import threading
# Warning, the "threading" module overwrites the built-in function enumerate()
# if used as import * !!

from .. import conf
from .systemcommand import SystemCommand, SystemCommandError
from . import ConfMgrError


class ApplicationError(ConfMgrError):
    """Exception concerning an application"""

    def __str__(self):
        return repr("ApplicationError : "+self.value)


class Application(object):
    """
    Provides methods for starting, stoping, validating applications
    @ivar mName: application name
    @type mName: C{str}
    @ivar mUsername: username to work as
    @type mUsername: C{str}
    @ivar mPriority: priority for restart ordering
    @type mPriority: C{int}
    @ivar mStartMethod: command to start the application
    @type mStartMethod: C{str}
    @ivar mStopMethod: command to stop the application
    @type mStopMethod: C{str}
    @ivar mValidationMethod: command to validate the application's
        configuration (on the target server)
    @type mValidationMethod: C{str}
    @ivar mQualificationMethod: command to qualify the application's
        configuration (on the ConfMgr server)
    @type mQualificationMethod: C{str}
    @ivar mServersList: list of servers where this application is deployed
    @type mServersList: C{list} of L{Server<lib.server.Server>}
    """

    def __init__(self, iName):
        """
        Constructor
        @param iName: Application name
        @type  iName: C{str}
        """
        self.mName = iName
        self.mServersList = None
        self.mUsername = "vigiconf"
        self.serversQueue = None # will be initialized as Queue.Queue later
        self.returnsQueue = None # will be initialized as Queue.Queue later
        _AppConfig = conf.apps[iName]
        self.mPriority = _AppConfig['priority']
        self.mStartMethod = _AppConfig['startMethod']
        self.mStopMethod = _AppConfig['stopMethod']
        self.mValidationMethod = _AppConfig['validationMethod']
        self.mQualificationMethod = _AppConfig['qualificationMethod']


    def __str__(self):
        """
        @return: String representation of the instance
        @rtype: C{str}
        """
        return self.getName()

    # accessors
    def getName(self):
        """@return: L{mName}"""
        return self.mName

    def getPriority(self):
        """@return: L{mPriority}"""
        return self.mPriority

    def getStartMethod(self):
        """@return: L{mStartMethod}"""
        return self.mStartMethod

    def getStopMethod(self):
        """@return: L{mStopMethod}"""
        return self.mStopMethod

    def getValidationMethod(self):
        """@return: L{mValidationMethod}"""
        return self.mValidationMethod

    def getQualificationMethod(self):
        """@return: L{mQualificationMethod}"""
        return self.mQualificationMethod

    def getServers(self):
        """@return: L{mServersList}"""
        return self.mServersList

    def getServerAt(self, index):
        """
        @return: an element of L{mServersList}
        @param index: index of the element to return
        @type  index: C{int}
        """
        return self.mServersList[index]

    # mutators
    def setName(self, iName):
        """Sets L{mName}"""
        self.mName = iName

    def setPriority(self, iPriority):
        """Sets L{mPriority}"""
        self.mPriority = iPriority

    def setStartMethod(self, iStartMethod):
        """Sets L{mStartMethod}"""
        self.mStartMethod = iStartMethod

    def setStopMethod(self, iStopMethod):
        """Sets L{mStopMethod}"""
        self.mStopMethod = iStopMethod

    def setValidationMethod(self, iVM):
        """Sets L{mValidationMethod}"""
        self.mValidationMethod = iVM

    def setQualificationMethod(self, iQM):
        """Sets L{mQualificationMethod}"""
        self.mQualificationMethod = iQM

    def setServers(self, iServersList):
        """Sets L{mServersList}"""
        self.mServersList = iServersList

    def setUsername(self, iUsername):
        """Sets L{mUsername}"""
        self.mUsername = iUsername

    # methods

    def getGroup(self):
        """Get the app's group"""
        appgroup = None
        for group, appnames in conf.appsByAppGroups.iteritems():
            if self.getName() in appnames:
                appgroup = group
                break
        if appgroup is None:
            raise ApplicationError("Can't find the appgroup for app %s" \
                                   % self.getName())
        return appgroup

    def filterServers(self, iServers):
        """
        @param iServers: the list of servers to filter on
        @type  iServers: C{list} of L{Server<lib.server.Server>}
        @returns: The intersection between iServers and our own servers list.
        """
        servernames = [ s.getName() for s in self.getServers() ]
        returnvalue = []
        for server in iServers:
            # Compare on the name
            if server.getName() in servernames:
                returnvalue.append(server)
        return returnvalue

    def manageReturnQueue(self):
        """
        Syslogs all the error strings that are in the return queue
        """
        _result = True # we suppose there is no error (empty queue)
        while not self.returnsQueue.empty(): # syslog each item of the queue
            _result = False
            _error = self.returnsQueue.get()
            syslog.syslog(syslog.LOG_WARNING, "%s" % _error)
        return _result


    def validate(self, iBaseDir):
        """
        Validates all the configuration files (starts the validation command)
        @param iBaseDir: The directory where the validation scripts are
        @type  iBaseDir: C{str}
        """ 
        # iterate through the servers
        for server in self.getServers():
            try:
                self.validateServer(iBaseDir, server)
            except ApplicationError:
                raise

    def validateServer(self, iBaseDir, iServer):
        """
        Validates all the configuration files (starts the validation command)
        on the specified server
        @param iBaseDir: The directory where the validation scripts are
        @type  iBaseDir: C{str}
        @param iServer: The server to validate on
        @type  iServer: L{Server<lib.server.Server>}
        """
        # iterate through the servers
        _validationCommand = self.getValidationMethod()
        if len(_validationCommand) > 0: # if there's a command for validation
            _commandStr = _validationCommand + " " + iBaseDir + "/" + iServer.getName()
            _command = SystemCommand(_commandStr)
            try:
                _command.execute()
            except SystemCommandError, e:
                raise ApplicationError("%s : Validation failed for : %s "
                                       % (self.getName(), iServer)
                                      +"- REASON %s" % e.value)    
        syslog.syslog(syslog.LOG_INFO, "%s : Validation successful for "
                                   % self.getName() + "server: %s" % iServer)



    def qualify(self):
        """
        Qualifies all the configuration files (starts the qualification command
        on each server)
        """
        # iterate through the servers
        for server in self.getServers():
            try:
                self.qualifyServer(server)
            except ApplicationError:
                raise

    def qualifyServers(self, iServers):
        """
        Qualifies the configuration files on the provided servers.
        @param iServers: The servers to qualify on
        @type  iServers: C{list} of L{Server<lib.server.Server>}
        """
        for _srv in self.filterServers(iServers):
            # can be threaded 1 thread per server
            self.qualifyServer(_srv)



    def qualifyServer(self, iServer):
        """
        qualifies all the configuration files (starts the qualification
        command) on a given server
        @param iServer: The server to qualify on
        @type  iServer: L{Server<lib.server.Server>}
        """
        # iterate through the servers
        qualificationCommand = self.getQualificationMethod()
        if len(qualificationCommand) > 0:
            _commandStr = "cd %s/new/ && sudo %s %s/new" \
                          % (conf.TARGETCONFDIR,
                             self.getQualificationMethod(), 
                             conf.TARGETCONFDIR)
            _command = iServer.createCommand(_commandStr)
            try:
                _command.execute()
            except SystemCommandError, e:
                raise ApplicationError("%s : Qualification failed on : %s - "
                                       % (self.getName(), iServer.getName())
                                      +"REASON : %s" % e.value)
        syslog.syslog(syslog.LOG_INFO, "%s : Qualification successful on "
                                       % self.getName() + "server : %s"
                                       % iServer.getName())


    def startThread(self):
        """Starts applications on a server taken from the top of the queue""" 
        _server = self.serversQueue.get()
        try:
            self.startServer(_server)
        except ApplicationError, e:
            self.returnsQueue.put(e.value)

        self.serversQueue.task_done()   

    def startOn(self, iServers):
        """
        Start the application on the intersection between iServers and our own
        servers list.
        @param iServers: The servers to start the application on
        @type  iServers: C{list} of L{Server<lib.server.Server>}
        """
        result = True

        self.serversQueue = Queue.Queue()
        self.returnsQueue = Queue.Queue()

        # intersection of serverslists
        _servers = self.filterServers(iServers)
        for _server in _servers:
            # fill the application queue
            self.serversQueue.put(_server)

        # start the threads
        for _server in _servers:
            _thread = threading.Thread(target = self.startThread)
            _thread.start()

        # wait until the queue is empty
        self.serversQueue.join()

        result = self.manageReturnQueue()
        if result == False:
            raise ApplicationError("%s : Start process failed." \
                                   % (self.getName()))

    def start(self):
        """Starts the application"""
        result = True

        self.serversQueue = Queue.Queue()
        self.returnsQueue = Queue.Queue()

        for _server in self.getServers():
            # fill the application queue
            self.serversQueue.put(_server)

        # start the threads
        for _server in self.getServers():
            _thread = threading.Thread(target = self.startThread)
            _thread.start()

        # wait until the queue is empty
        self.serversQueue.join()

        result = self.manageReturnQueue()
        if result == False:
            raise ApplicationError("%s : Start process failed." \
                                   % (self.getName()))


    def startServer(self, iServer):
        """
        Starts the application on the specified server
        @param iServer: The server to start the application on
        @type  iServer: L{Server<lib.server.Server>}
        """
        if len(self.getStartMethod()) > 0:
            syslog.syslog(syslog.LOG_INFO,
                          "Starting %s on %s ...\n" \
                          % (self.getName(), iServer.getName()))
            _commandStr = "sudo " + self.getStartMethod()
            _command = iServer.createCommand(_commandStr)
            try:
                _command.execute()
            except SystemCommandError, e:
                raise ApplicationError("Can't Start %s on %s - REASON %s\n" \
                               % (self.getName(), iServer.getName(), e.value))
            syslog.syslog(syslog.LOG_INFO,
                         ("%s started on %s\n" \
                         % (self.getName(), iServer.getName())))

    def stopThread(self):
        """Stops applications on a server taken from the top of the queue"""
        _server = self.serversQueue.get()
        try:
            self.stopServer(_server)
        except ApplicationError, e:
            self.returnsQueue.put(e.value)
        self.serversQueue.task_done()   

    def stopOn(self, iServers):
        """
        Stop the application on the intersection between iServers and our own
        servers list.
        @param iServers: The servers to stop the application on
        @type  iServers: C{list} of L{Server<lib.server.Server>}
        """
        result = True

        self.serversQueue = Queue.Queue()
        self.returnsQueue = Queue.Queue()
        _servers = self.filterServers(iServers)
        for _server in _servers:
            # fill the application queue
            self.serversQueue.put(_server)

        # start the threads
        for _server in _servers:
            _thread = threading.Thread(target = self.stopThread)
            _thread.start()

        # wait until the queue is empty
        self.serversQueue.join()

        result = self.manageReturnQueue()
        if result == False:
            raise ApplicationError("%s : Stop process failed." \
                                   % (self.getName()))

    def stop(self):
        """Stops the applications"""
        result = True

        self.serversQueue = Queue.Queue()
        self.returnsQueue = Queue.Queue()

        for _server in self.getServers():
            # fill the application queue
            self.serversQueue.put(_server)

        # start the threads
        for _server in self.getServers():
            _thread = threading.Thread(target = self.stopThread)
            _thread.start()

        # wait until the queue is empty
        self.serversQueue.join()

        result = self.manageReturnQueue()
        if result == False :
            raise ApplicationError("%s : Stop process failed." \
                                   % (self.getName()))


    def stopServer(self, iServer):
        """
        Stops the application on a given server
        @param iServer: The server to stop the application on
        @type  iServer: L{Server<lib.server.Server>}
        """
        if (len(self.getStopMethod()) > 0):
            syslog.syslog(syslog.LOG_INFO, "Stopping %s on %s ...\n" \
                                       % (self.getName(), iServer.getName()))
            _commandStr = "sudo " + self.getStopMethod()
            _command = iServer.createCommand(_commandStr)
            try:
                _command.execute()
            except SystemCommandError, e:
                raise ApplicationError("Can't Stop %s on %s - REASON %s\n" \
                               % (self.getName(), iServer.getName(), e.value))
            syslog.syslog(syslog.LOG_INFO,
                         ("%s stopped on %s\n" \
                          % (self.getName(), iServer.getName())))


# vim:set expandtab tabstop=4 shiftwidth=4:
