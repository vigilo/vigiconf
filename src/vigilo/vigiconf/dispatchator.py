#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
This module is in charge of controling all the deployement/validation process
of a new configuration.

This is the module to call as a main end-user command line (see --help)
"""

from __future__ import absolute_import

import locale
import fcntl
import traceback
import os
import sys
import Queue # Requires: python >= 2.5
from optparse import OptionParser
from threading import Thread
import shutil

from vigilo.common.conf import settings
settings.load_module(__name__)

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

#from vigilo.models.configure import configure_db
#configure_db(settings['database'], 'sqlalchemy_',
#    settings['database']['db_basename'])
#
#from vigilo.models.session import metadata
#metadata.create_all()

from . import conf
from . import generator
from .lib.application import Application, ApplicationError
from .lib.systemcommand import SystemCommand, SystemCommandError
from .lib import VigiConfError
from .lib.server import ServerFactory, ServerError
from .lib import dispatchmodes


class DispatchatorError(VigiConfError):
    """The exception type raised by instances of Dispatchator"""

    def __init__(self, value):
        """
        @param value: A message explaining this exception.
        @type  value: C{str}
        """
        super(DispatchatorError, self).__init__(value)
        self.value = value

    def __str__(self):
        """
        String representation of an instance of this exception.
        @rtype: C{str}.
        """
        return repr("DispatchatorError : "+self.value)

class Dispatchator(object):
    """
    Dispatch the configurations files for all the applications

    @ivar mServers: servers that will be used for operations
    @type mServers: C{list} of L{Server<lib.server.Server>}
    @ivar mApplications: applications deployed on L{mServers}
    @type mApplications: C{list} of L{Application<lib.application.Application>}
    @ivar mModeForce: defines if the --force option is set
    @type mModeForce: C{boolean}
    @ivar mAppsList: list of all the applications contained in the configuration.
    @type mAppsList: C{list} of C{str}
    @ivar commandsQueue: commands queue
    @type commandsQueue: L{Queue}
    @ivar returnsQueue: commands queue
    @type returnsQueue: L{Queue}
    @ivar deploy_revision:
    @type deploy_revision:
    """

    def __init__(self):
        self.mServers = []
        self.mApplications = []
        self.mModeForce = False
        self.mAppsList = []
        self.commandsQueue = None # will be initialized as Queue.Queue later
        self.returnsQueue = None # will be initialized as Queue.Queue later
        self.deploy_revision = None
        
        self.mode_db = 'commit'
        # mode simulation: on recopie simplement la commande svn pour
        # verification
        try:
            self.simulate = settings["vigiconf"].as_bool("simulate")
        except KeyError:
            self.simulate = False
        self.svn_cmd = ""
        
        # initialize applications
        self.listApps()
        self.sortApplication()


    def getAppsList(self):
        """
        @returns: L{mAppsList}
        """
        return self.mAppsList

    def getServersList(self):
        """
        @returns: The names of the servers
        @rtype:   C{list} of C{str}
        """
        return [ s.getName() for s in self.getServers() ]

    def getServers(self):
        """
        @returns: L{mServers}
        """
        return self.mServers

    def getApplications(self):
        """
        @returns: L{mApplications}
        """
        return self.mApplications

    def getModeForce(self): 
        """
        @returns: L{mModeForce}
        """
        return self.mModeForce

    def setAppsList(self, iAppsList):
        """
        Mutator on L{mAppsList}
        @type iAppsList: C{list} of C{str}
        """
        self.mAppsList = iAppsList

    def setServers(self, iServers):
        """
        Mutator on L{mServers}
        @type iServers: C{list} of L{Server<lib.server.Server>}
        """
        self.mServers = iServers

    def setApplications(self, iApplications):
        """
        Mutator on L{mApplications}
        @type iApplications: C{list} of L{Application
            <lib.application.Application>}
        """
        self.mApplications = iApplications

    def setModeForce(self, iBool):
        """
        Mutator on L{mModeForce}
        @type iBool: C{boolean}
        """
        self.mModeForce = iBool    

    # methods
    def restrict(self, servers):
        """
        Restrict applications and servers to the ones given as arguments.
        @note: This method has to be implemented by subclasses
        @param servers: Server names.
        @type  servers: C{list} of C{str}
        """
        pass

    def addApplication(self, iApp):
        """
        Appends an Application to the list of Applications.
        @type iApp: L{Application<lib.application.Application>}
        """
        self.mAppsList.append(iApp)

    def createCommand(self, iCommandStr):
        """
        Create a new system command
        @param iCommandStr: Command to execute
        @type  iCommandStr: C{str}
        @rtype: L{SystemCommand<lib.systemcommand.SystemCommand>}
        """
        return SystemCommand(iCommandStr, simulate=self.simulate)

    def listApps(self):
        """
        Get all applications from configuration, and fill the L{mApplications}
        variable.
        """
        apps = set()
        for appnames in conf.appsByAppGroups.values():
            for appname in appnames:
                apps.add(appname)
        _applications = []
        for appname in apps:
            if not conf.apps.has_key(appname):
                raise DispatchatorError("%s unknown" % appname)
            _AppConfig = conf.apps[appname]
            _App = Application(appname)
            _App.setServers(
                self.buildServersFrom(
                    self.getServersForApp(_App)
                    )
                )
            _applications.append(_App)
        self.setApplications(_applications)

    def getServersForApp(self, app):
        """
        Get the list of server names for this application.
        @note: To be implemented by subclasses.
        @param app: Application to analyse
        @type  app: L{Application<lib.application.Application>}
        @return: Server names for this application
        @rtype: C{list} of C{str}
        """
        pass

    def buildServersFrom(self, iServers):
        """
        Builds and returns a list of servers objects.
        @param iServers: List of server names to build from
        @type  iServers: C{list} of C{str}
        @rtype: C{list} of L{Server<lib.server.Server>}
        """
        _servers = []
        serverfactory = ServerFactory()
        for _srv in iServers:
            _srvobj = serverfactory.makeServer(_srv)
            _servers.append(_srvobj)
        return _servers

    def sortApplication(self):
        """
        Sorts our applications by priority. The sorting is done in-place in the
        L{mAppsList} variable.
        """       
        self.getAppsList().sort(reverse=True,
                    cmp=lambda x,y: cmp(x.getPriority(), y.getPriority()))

    #Generate Configuration
    def generateConfig(self):
        """
        Generate the configuration files for the servers, using the
        L{generator} module.
        
        Selon l'option --modedb les données sont commitées ou non
        dans la base de données; ceci afin de retrouver l'état précédent
        facilement si le déploiement ne se passe pas correctement.
        """
        # generate conf files
        gendir = os.path.join(settings["vigiconf"].get("libdir"), "deploy")
        shutil.rmtree(gendir, ignore_errors=True)
        
        result = generator.generate(commit_db=(self.mode_db == 'commit'))
        if not result:
            raise DispatchatorError("Can't generate configuration")

    def saveToConfig(self):
        """
        Generate, validate and commit the last revision of the files via SVN
        """
        #Generate Configuration
        self.generateConfig()

        #Validate Configuration
        for _App in self.getApplications():
            _App.validate(os.path.join(settings["vigiconf"].get("libdir"),
                                       "deploy"))
        LOGGER.info("Validation Successful")

        #Commit Configuration
        self.commitLastRevision()
        LOGGER.info("Commit Successful")
    
    
    def loadRevision(self, revision):
        """
        Load a given revision in the configuration directory.
        """
        confdir = settings["vigiconf"].get("confdir")
        
        if not settings["vigiconf"].get("svnrepository", False):
            raise DispatchatorError(
                "Not revision load because the 'svnrepository' configuration "
                +"parameter is empty\n")
                
        _cmd = self._get_auth_svn_cmd_prefix('update')
        
        _cmd += '--revision %s ' % revision
        _cmd +=  '%s %s' % (
                    settings["vigiconf"].get("svnrepository"),
                    confdir
                    )
        
        _command = self.createCommand(_cmd)
        
        if self.simulate:
            self.svn_cmd = _cmd
        
        try:
            _command.execute()
        except SystemCommandError, e:
            raise DispatchatorError(
                    "Can't execute the request to load %s " % revision
                    +"revision. REASON: %s" % e.value)
        
    
    def commitLastRevision(self):
        """
        Commit the last revision of the files via SVN
        @return: the number of the revision
        @rtype: C{int}
        """
        confdir = settings["vigiconf"].get("confdir")
        
        if not settings["vigiconf"].get("svnrepository", False):
            LOGGER.warning("Not committing because the 'svnrepository' "
                           "configuration parameter is empty")
            return 0
        
        _cmd = self._get_auth_svn_cmd_prefix('ci')
        
        _cmd += "-m 'Auto generate configuration %s' %s" % \
                    (confdir, confdir)
        _command = self.createCommand(_cmd)
        
        try:
            _command.execute()
        except SystemCommandError, e:
            raise DispatchatorError(
                    "Can't execute the request to commit %s " % confdir
                    +"revision. REASON: %s" % e.value)
        return self.getLastRevision()
    
    
    def _get_auth_svn_cmd_prefix(self, svn_cmd):
        """
        Get an authentified svn command prefix like
          "svn <svn_cmd> --username user --password password "
        
        @return: the svn command prefix
        @rtype: C{str}
        """
        _cmd = "svn %s " % svn_cmd
        svnusername = settings["vigiconf"].get("svnusername", False)
        svnpassword =  settings["vigiconf"].get("svnpassword", False)
        if svnusername and svnpassword: # TODO: escape password
            _cmd += "--username %s --password %s " % \
                    (svnusername, svnpassword)
        return _cmd
        

    def getLastRevision(self):
        """
        Get the last revision of the files via SVN
        @return: the number of the current revision
        @rtype: C{int}
        """
        res = 0
        if not settings["vigiconf"].get("svnrepository", False):
            return res
        # <code> UNIX only
        # TODO: use svn info --xml and parse it
        _command = self.createCommand("LANG=C LC_ALL=C svn info -r HEAD %s" % 
                                     settings["vigiconf"].get("svnrepository"))
        try:
            _command.execute()
        except SystemCommandError, e:
            raise DispatchatorError("Can't execute the request to get the "
                                   +"current revision.REASON %s" % e.value)

        lines = _command.getResult().split("\n")
        for line in lines:
            if line.startswith("Revision: "):    
                rev = line.strip().split(": ")[1]
                res = locale.atoi(rev)
                break 
        return res

    def updateLocalCopy(self, iRevision):
        """
        Updates the local copy of the repository
        @param iRevision: SVN revision to update to
        @type  iRevision: C{int}
        """
        if not settings["vigiconf"].get("svnrepository", False):
            LOGGER.warning("Not updating because the 'svnrepository' "
                           "configuration parameter is empty")
            return 0
        _cmd = "svn up "
        svnusername = settings["vigiconf"].get("svnusername", False)
        svnpassword =  settings["vigiconf"].get("svnpassword", False)
        if svnusername and svnpassword: # TODO: escape password
            _cmd += "--username %s --password %s " % \
                    (svnusername, svnpassword)
        _cmd += "-r %d %s" % (iRevision, settings["vigiconf"].get("confdir"))
        _command = self.createCommand(_cmd)
        try:
            _command.execute()
        except SystemCommandError, e:
            raise DispatchatorError("Can't execute the request to update the "
                                   +"local copy. COMMAND %s FAILED. REASON: %s"
                                   % (_cmd, e.value) )

    def manageReturnQueue(self):
        """
        Manage the data in the return queue. Syslogs all the items.
        @rtype: C{int}
        """
        _result = True # we suppose there is no error (empty queue)
        while not self.returnsQueue.empty(): # syslog each item of the queue
            _result = False
            _error = self.returnsQueue.get()
            LOGGER.error(str(_error))
        return _result

    def actionThread(self, iAction, iServers):
        """
        Implementation of a thread 
        @param iAction: Function to execute in the thread
        @type  iAction: callable
        @param iServers: List of servers, will be passed to the iAction
            function as second argument
        @type  iServers: C{list} of L{Server<lib.server.Server>}
        """
        # get the object from Queue
        _object = self.commandsQueue.get()
        # does the action on this server
        try:
            iAction(_object, iServers)
        except VigiConfError, e: # if it fails
            self.returnsQueue.put(e.value)
        self.commandsQueue.task_done()
        
    
    def deploysOnServers(self, iServers, iRevision):
        """
        Deploys the config files to the servers belonging to iServers
        @param iServers: List of servers
        @type  iServers: C{list} of L{Server<lib.server.Server>}
        @param iRevision: SVN revision number
        @type  iRevision: C{int}
        """
        try:
            if len(iServers) > 0:
                ## update the local files
                self.updateLocalCopy(iRevision)
                ## generate the deployment directory
                self.generateConfig()
                self.threadedDeployFiles(iServers, iRevision)
        except DispatchatorError, e:
            raise e

    def threadedDeployFiles(self, iServers, iRevision):
        """
        Deploy the files to each server of iServers. One thread is created for
        each server
        @param iServers: List of servers
        @type  iServers: C{list} of L{Server<lib.server.Server>}
        @param iRevision: SVN revision number
        @type  iRevision: C{int}
        """
        self.commandsQueue = Queue.Queue()
        self.returnsQueue = Queue.Queue()
        for _srv in iServers:
            self.commandsQueue.put(_srv)
            _thread = Thread(target=self.serverDeployFiles, args=[iRevision])
            _thread.start()
        self.commandsQueue.join()
        _result = self.manageReturnQueue()
        if not _result:
            raise DispatchatorError("The configurations files have not been "
                                   +"transfered on every server. See above "
                                   +"for more information.")

    def serverDeployFiles(self, iRevision):
        """
        Method called by L{threadedDeployFiles} to deploy the files in the
        specified SVN revision
        @param iRevision: SVN revision number
        @type  iRevision: C{int}
        """
        _srv = self.commandsQueue.get()
        try:
            _srv.deploy(iRevision)
        except VigiConfError, e: # if it fails
            self.returnsQueue.put(e.value)
        self.commandsQueue.task_done()

    #  configuration qualification    
    def qualifyOnServers(self, iServers):
        """
        Qualify applications on the specified servers list
        @param iServers: List of servers
        @type  iServers: C{list} of L{Server<lib.server.Server>}
        """
        # qualify applications on those servers
        for _app in self.getApplications():
            _app.qualifyServers(iServers)

    def deploy(self):
        """
        Does a full deployment: deploy files, qualify files
        """
        _servers = []
        
        if self.deploy_revision:
            # deploiment d'une révision donnée
            self.loadRevision(self.deploy_revision)
            _revision = self.deploy_revision
        else:
            # get the last revision on SVN
            _revision = self.getLastRevision()
            
        # 1 - build a list of servers that requires deployment
        if self.getModeForce() == False: 
            for _srv in self.getServers():
                # TODO: si deploy_revision, faire quelque chose
                _srv.updateRevisionManager()
                _srv.getRevisionManager().setSubversion(_revision)
                if _srv.needsDeployment():
                    _servers.append(_srv)
            if len(_servers) <= 0:
                LOGGER.info("All servers are up-to-date. Nothing to do.")
        else: # by default, takes all the servers  
            _servers = self.getServers()
        # 2 - deploy on those servers
        self.deploysOnServers(_servers, _revision)
        # 3 - qualify deployed configurations
        self.qualifyOnServers(_servers)

    def startOrStopApplications(self, fAction, fArgs, iErrorMessage):
        """
        Does a start or a stop action depending on the method fAction
        @param fAction: method to call
        @type  fAction: callable
        @param fArgs: list of arguments for the function
        @type  fArgs: list
        @param iErrorMessage: message if the function fails
        @type  iErrorMessage: C{str}
        """
        _result = True
        _Apps = self.getApplications()
        _CurrentLevel = 0

        if len(_Apps) == 0:
            return

        _application = _Apps[0]
        _CurrentLevel = _application.getPriority()

        self.commandsQueue = Queue.Queue()
        self.returnsQueue = Queue.Queue()
        for _application in _Apps:
            if (_application.getPriority() == _CurrentLevel):
                # fill the application queue
                self.commandsQueue.put(_application)
                _thread = Thread(target=fAction, args=fArgs)
                _thread.start()

            else:
                # wait until the queue is empty
                self.commandsQueue.join()
                _CurrentLevel = _application.getPriority()

                # fill the application queue
                self.commandsQueue.put(_application)

                _thread = Thread(target=fAction, args=fArgs)
                _thread.start()
        # wait until the queue is empty
        self.commandsQueue.join()

        _result = self.manageReturnQueue()
        if (_result == False) :
            raise DispatchatorError(iErrorMessage)

    def applicationStop(self, iApplication, iServers):
        """
        Stops iApplication on each server in iServers
        @param iApplication: application to stop
        @type  iApplication: L{Application<lib.application.Application>}
        @param iServers: List of servers
        @type  iServers: C{list} of L{Server<lib.server.Server>}
        """
        iApplication.stopOn(iServers)

    def stopThread(self, iServers):
        """
        Thread method to stop an application on a servers list
        @param iServers: List of servers
        @type  iServers: C{list} of L{Server<lib.server.Server>}
        """
        self.actionThread(self.applicationStop, iServers)

    def applicationStart(self, iApplication, iServers):
        """
        Starts the given application on each server in iServers
        @param iApplication: application to start
        @type  iApplication: L{Application<lib.application.Application>}
        @param iServers: List of servers
        @type  iServers: C{list} of L{Server<lib.server.Server>}
        """
        iApplication.startOn(iServers) 

    def startThread(self, iServers):
        """
        Starts the next application on each server in iServers
        @param iServers: List of servers
        @type  iServers: C{list} of L{Server<lib.server.Server>}
        """ 
        self.actionThread(self.applicationStart, iServers)

    def switchDirectoriesOn(self, iServers):
        """
        Switch directories prod->old and new->prod, but only on servers that
        require it (except in force mode)
        @param iServers: List of servers
        @type  iServers: C{list} of L{Server<lib.server.Server>}
        """
        self.threadedSwitchDirectories(iServers)


    def threadedSwitchDirectories(self, iServers):
        """
        Executes a thread for each server in iServers. Each thread will switch
        directories on the appropriate server.
        @param iServers: List of servers
        @type  iServers: C{list} of L{Server<lib.server.Server>}
        """
        self.commandsQueue = Queue.Queue()
        self.returnsQueue = Queue.Queue()
        for _srv in iServers:
            self.commandsQueue.put(_srv)
            _thread = Thread(target=self.serverSwitchDirectories)
            _thread.start()
        self.commandsQueue.join()
        _result = self.manageReturnQueue()
        if not _result:
            raise DispatchatorError("Switch directories was not successful "
                                   +"on each server.")

    def serverSwitchDirectories(self):
        """
        Calls switchDirectories() on the first server in the commandsQueue
        """
        _srv = self.commandsQueue.get()
        try:
            _srv.switchDirectories()
        except VigiConfError, e: # if it fails
            self.returnsQueue.put(e.value)
        self.commandsQueue.task_done()

    def restart(self):
        """Does a full restart on all the servers"""
        _servers = []
        _revision = self.getLastRevision() # get the last revision on SVN
        # 1 - build a list of servers that requires restart
        if self.getModeForce() == False: 
            for _srv in self.getServers():
                _srv.updateRevisionManager()
                _srv.getRevisionManager().setSubversion(_revision)
                if _srv.needsRestart():
                    _servers.append(_srv)
                if _srv.needsDeployment():
                    LOGGER.info("Server %s should be deployed." % _srv.getName())
            if len(_servers) <= 0:
                LOGGER.info("All servers are up-to-date. No restart needed.")
        else: # by default, takes all the servers  
            _servers = self.getServers()
        # do the operations
        self.restartServers(_servers)

    def restartServers(self, iServers):
        """
        Restart all the specified servers
        @param iServers: List of servers
        @type  iServers: C{list} of L{Server<lib.server.Server>}
        """
        self.stopApplicationsOn(iServers)
        self.switchDirectoriesOn(iServers)
        self.startApplicationsOn(iServers)

    def stopApplications(self):
        """Stops all the applications on all the servers"""
        self.stopApplicationsOn(self.getServers())

    def stopApplicationsOn(self, iServers):
        """
        Stop all the application on the specified servers
        @param iServers: List of servers
        @type  iServers: C{list} of L{Server<lib.server.Server>}
        """
        if len(iServers) > 0:
            _servers = []
            for _srv in iServers:
                _servers.append(_srv)
            self.startOrStopApplications(self.stopThread, [_servers],
                                        "Stop applications failed\n")

    def startApplications(self):
        """Starts all the applications on all the servers"""
        self.startApplicationsOn(self.getServers())

    def startApplicationsOn(self, iServers):
        """
        Starts all the application on the servers in iServers
        @param iServers: List of servers
        @type  iServers: C{list} of L{Server<lib.server.Server>}
        """
        if len(iServers) > 0:
            _servers = []
            for _srv in iServers:
                _servers.append(_srv)
            self.startOrStopApplications(self.startThread, [_servers],
                                        "Start applications failed\n")

    # Undo
    def undo(self):
        """Performs an "undo" on the configuration files"""
        for _srv in self.getServers():
            try:
                _srv.undo()
            except ServerError, se:
                LOGGER.exception(se)


    def printState(self):
        """Prints a summary"""
        _revision = self.getLastRevision()
        print("Current revision in the repository : %d"%(_revision))
        for _srv in self.getServers():
            try:
                _srv.updateRevisionManager()
                _srv.getRevisionManager().setSubversion(_revision)
                _deploymentStr = ""
                _restartStr = ""
                if _srv.needsDeployment():
                    _deploymentStr = "(should be deployed)"
                if _srv.needsRestart():
                    _restartStr = "(should restart)"
                print "Revisions for server %s : %s%s%s" % \
                      (_srv.getName(), str(_srv.getRevisionManager()),
                       _deploymentStr, _restartStr)
            except Exception, e:
                LOGGER.warning("Cannot get revision for server: %s. "
                               "REASON : %s", _srv.getName(), str(e))



#def main():
#    """Parses the commandline and starts the requested actions"""    
#
#    parser = OptionParser() # options and arguments parser
#    # declare all options
#    parser.add_option("-f", "--force", action="store_true", dest="force",
#                      help="Force the immediate execution of the command. "
#                          +"Do not wait. Bypass all checks.")
#    parser.add_option("-c", "--commit", action="store_true",
#                      dest="saveToConfig", help="Commits a new configuration.")
#    parser.add_option("-d", "--deploy", action="store_true", dest="deploy",
#                      help="Deploys the configuration on each server if this "
#                          +"configuration has changed.")
#    parser.add_option("-r", "--restart", action="store_true", dest="restart",
#                      help="Restart all the applications if a new "
#                          +"configuration has been deployed. "
#                          +"(stop, refactor, start)")
#    parser.add_option("-x", "--stop", action="store_true", dest="stop",
#                      help="Stop all the applications.")
#    parser.add_option("-s", "--start", action="store_true", dest="start",
#                      help="Start all the applications.")
#    parser.add_option("-u", "--undo", action="store_true", dest="undo",
#                      help="Deploys the previously installed configuration. "
#                          +"2 consecutives undo will return to the "
#                          +"configuration that was installed before the "
#                          +"first undo (ie. redo). Cannot be used with any "
#                          +"other option. Should be followed by the restart "
#                          +"command.")
#    parser.add_option("-v", "--revision", action="store", dest="revision",
#                      help="Deploy the given revision. Should be used with"
#                          +" --deploy option. Should be followed by the"
#                          +" restart command.")
#    parser.add_option("-i", "--info", action="store_true", dest="info",
#                      help="Prints a summary of the actual configuration.")
#    parser.add_option("-n", "--dry-run", action="store_true", dest="simulate",
#                      help="Simulate only, no copy will be actually made,"
#                          +"no commit in the database.")
#
#
#    # parse the command line
#    (options, args) = parser.parse_args()
#
#    try:
#        conf.loadConf()
#    except Exception, e :
#        LOGGER.error("Cannot load the configuration: %s", e)
#        sys.exit(1)
#
#    _dispatchator = dispatchmodes.getinstance()
#
#    # Limit the server list to the ones on the command line
#    _dispatchator.restrict(args)
#
#    # Handle command-line options
#    if (options.simulate):
#        settings["vigiconf"]["simulate"] = True
#        # pas de commit sur la base de données
#        _dispatchator.mode_db = 'no_commit'
#        
#    if (options.force):
#        _dispatchator.setModeForce(True)
#    
#    if (options.revision):
#        _dispatchator.deploy_revision = int(options.revision)
#
#    if ( len(_dispatchator.getServers()) <= 0):
#        LOGGER.warning("No server to manage.")
#    else:
#
#        # if "restart" is selected, then all the corresponding actions are
#        # selected too
#        if (options.restart):
#            parser.values.restart = True
#            parser.values.stop = True
#            parser.values.start = True
#
#
#        # executes all requested commands
#        try:
#            if options.info:
#                _dispatchator.printState()
#            if options.undo:
#                _dispatchator.undo()
#            if options.saveToConfig:
#                _dispatchator.saveToConfig()
#            if options.deploy:     
#                _dispatchator.deploy()
#            if options.restart:
#                _dispatchator.restart()
#            else:
#                if options.stop:
#                    _dispatchator.stopApplications()
#                if options.start:
#                    _dispatchator.startApplications()
#                else:
#                    msg = "You did not ask me to do anything. Use '--help' for the available actions."
#                    parser.error(msg)
#        except (DispatchatorError, ApplicationError), e:
#            LOGGER.exception(e)
#
#if __name__ == "__main__":
#    LOGGER.info("Dispatchator Begin")
#
#    f = open(settings["vigiconf"].get("lockfile"),'a+')
#    try:
#        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
#    except Exception, exp:
#        LOGGER.error("Can't obtain lock on lockfile. Dispatchator already "
#                    +"running ? REASON : %s", exp)
#        sys.exit(1)
#    try:
#        main()
#    except Exception, exp:
#        LOGGER.exception("Execution error.REASON : %s", exp)
#        #for l in traceback.format_exc().split("\n"):
#        #    LOGGER.error(l)
#    LOGGER.info("Dispatchator End")


# vim:set expandtab tabstop=4 shiftwidth=4:
