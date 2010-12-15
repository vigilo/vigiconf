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
#from optparse import OptionParser
from threading import Thread
import shutil
from xml.etree import ElementTree as ET

from pkg_resources import working_set

from vigilo.common.conf import settings
settings.load_module(__name__)

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)


from vigilo.vigiconf import conf
from .generators import GeneratorManager
from .application import Application, ApplicationError
from .systemcommand import SystemCommand, SystemCommandError
from . import VigiConfError
from .server import ServerFactory, ServerError
from . import dispatchmodes


class DispatchatorError(VigiConfError):
    """The exception type raised by instances of Dispatchator"""

    pass

class Dispatchator(object):
    """
    Dispatch the configurations files for all the applications

    @ivar mServers: servers that will be used for operations
    @type mServers: C{list} of L{Server<lib.server.Server>}
    @ivar applications: applications deployed on L{mServers}
    @type applications: C{list} of L{Application<lib.application.Application>}
    @ivar mModeForce: defines if the --force option is set
    @type mModeForce: C{boolean}
    @ivar commandsQueue: commands queue
    @type commandsQueue: L{Queue}
    @ivar returnsQueue: commands queue
    @type returnsQueue: L{Queue}
    @ivar deploy_revision: the SVN revision to deploy
    @type deploy_revision: C{str}
    """

    def __init__(self):
        self.mServers = []
        self.applications = []
        self.mModeForce = False
        self.commandsQueue = None # will be initialized as Queue.Queue later
        self.returnsQueue = None # will be initialized as Queue.Queue later
        self.deploy_revision = "HEAD"

        self.mode_db = 'commit'
        # mode simulation: on recopie simplement la commande svn pour
        # verification
        try:
            self.simulate = settings["vigiconf"].as_bool("simulate")
        except KeyError:
            self.simulate = False

        # initialize applications
        self.listApps()
        self.applications.sort(reverse=True, key=lambda a: a.priority)


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

    def getModeForce(self):
        """
        @returns: L{mModeForce}
        """
        return self.mModeForce

    def setServers(self, iServers):
        """
        Mutator on L{mServers}
        @type iServers: C{list} of L{Server<lib.server.Server>}
        """
        self.mServers = iServers

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

    def createCommand(self, iCommand):
        """
        Create a new system command
        @param iCommand: Command to execute
        @type  iCommand: C{str}
        @rtype: L{SystemCommand<lib.systemcommand.SystemCommand>}
        """
        return SystemCommand(iCommand, simulate=self.simulate)

    def listApps(self):
        """
        Get all applications from configuration, and fill the L{applications}
        variable.
        """
        for entry in working_set.iter_entry_points(
                        "vigilo.vigiconf.applications"):
            appclass = entry.load()
            app = appclass()
            if app.name != entry.name:
                msg = _("Incoherent configuration: application %(app)s has an "
                        "entry point named %(epname)s in package %(eppkg)s")
                LOGGER.warning(msg % {"app": app.name, "epname": entry.name,
                                      "eppkg": entry.dist})
            if app.name not in conf.apps:
                LOGGER.info(_("Application %s is installed but disabled "
                              "(see conf.d/general/apps.py)") % app.name)
                continue
            if app.name in [ a.name for a in self.applications ]:
                msg = _("Application %s is not unique.") % app.name
                msg += _(" Providing modules: %s") \
                        % ", ".join(list(working_set.iter_entry_points(
                                "vigilo.vigiconf.applications", entry.name)))
                raise DispatchatorError(msg)
            app.servers = self.buildServersFrom(self.getServersForApp(app))
            self.applications.append(app)
        # Vérification : a-t-on déclaré une application non installée ?
        for listed_app in conf.apps:
            if listed_app not in [a.name for a in self.applications]:
                LOGGER.warning(_("Application %s has been added to "
                            "conf.d/general/apps.py, but is not installed")
                            % listed_app)

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

    def generate(self):
        """
        Génère la configuration des différents composants, en utilisant le
        L{GeneratorManager}.

        Après génération, la configuration est validée, et en cas de succès les
        fichiers de configuration de VigiConf sont comittés en SVN
        """
        if not self.run_generator():
            return False
        self.validate_generation()
        return True

    def run_generator(self):
        gendir = os.path.join(settings["vigiconf"].get("libdir"), "deploy")
        shutil.rmtree(gendir, ignore_errors=True)
        generator = GeneratorManager(self.applications, self)
        result = generator.generate(commit_db=(self.mode_db == 'commit'))
        return result

    def validate_generation(self):
        for _App in self.applications:
            _App.validate(os.path.join(settings["vigiconf"].get("libdir"),
                                       "deploy"))
        LOGGER.info(_("Validation Successful"))
        #Commit Configuration
        last_rev = self._svn_commit()
        if self.deploy_revision == "HEAD":
            self.deploy_revision = last_rev
        LOGGER.info(_("Commit Successful"))

    def prepare_svn(self):
        """
        Prepare the configuration dir (it's an SVN working directory)
        """
        status = self.get_svn_status()
        if self.deploy_revision != "HEAD" and \
                (status["add"] or status["remove"] or status["modified"]):
            raise DispatchatorError(_("You can't go back to a former "
                "revision if you have modified your configuration. "
                "Use 'svn revert' to cancel your modifications"))
        self._svn_sync(status)

    def get_svn_status(self):
        _cmd = self._get_auth_svn_cmd_prefix('status')
        _cmd.append("--xml")
        _cmd.append(settings["vigiconf"].get("confdir"))
        _command = self.createCommand(_cmd)
        try:
            result = _command.execute()
        except SystemCommandError, e:
            raise DispatchatorError(
                    _("Can't get the SVN status for the configuration dir: %s")
                      % e.value)
        status = {"add": [], "remove": [], 'modified': []}
        if not _command.getResult():
            return status
        output = ET.fromstring(_command.getResult(stderr=False))
        for entry in output.findall(".//entry"):
            state = entry.find("wc-status").get("item")
            if state == "unversioned":
                status["add"].append(entry.get("path"))
            elif state == "missing":
                status["remove"].append(entry.get("path"))
            elif state == "modified" or state == "added":
                status["modified"].append(entry.get("path"))
        return status

    def _svn_sync(self, status=None):
        if not settings["vigiconf"].get("svnrepository", False):
            LOGGER.warning(_("Not updating because the 'svnrepository' "
                               "configuration parameter is empty"))
            return 0
        if status is None:
            status = self.get_svn_status()
        for item in status["add"]:
            self._svn_add(item)
        for item in status["remove"]:
            self._svn_remove(item)
        self._svn_update()

    def _svn_add(self, path):
        LOGGER.debug(_("Adding a new configuration file to the repository: %s"), path)
        _cmd = ["svn", "add"]
        _cmd.append(path)
        _command = self.createCommand(_cmd)
        try:
            result = _command.execute()
        except SystemCommandError, e:
            raise DispatchatorError(
                    _("Can't add %(path)s in repository: %(error)s") % {
                        'path': path,
                        'error': e.value,
                    })
        return result

    def _svn_remove(self, path):
        LOGGER.debug(_("Removing an old configuration file from the repository: %s"), path)
        _cmd = self._get_auth_svn_cmd_prefix('remove')
        _cmd.append(path)
        _command = self.createCommand(_cmd)
        try:
            result = _command.execute()
        except SystemCommandError, e:
            raise DispatchatorError(
                    _("Can't remove %(path)s from repository: %(error)s") % {
                        'path': path,
                        'error': e.value,
                    })
        return result

    def _svn_commit(self):
        if not settings["vigiconf"].get("svnrepository", False):
            LOGGER.warning(_("Not committing because the 'svnrepository' "
                           "configuration parameter is empty"))
            return 0
        confdir = settings["vigiconf"].get("confdir")
        _cmd = self._get_auth_svn_cmd_prefix('ci')
        _cmd.extend(["-m", "Auto generate configuration %s" % confdir])
        _cmd.append(confdir)
        _command = self.createCommand(_cmd)
        try:
            _command.execute()
        except SystemCommandError, e:
            raise DispatchatorError(
                    _("Can't commit the configuration dir in SVN: %s")
                      % e.value)
        return self.getLastRevision()

    def _svn_update(self):
        """
        Updates the local copy of the repository
        """
        _cmd = self._get_auth_svn_cmd_prefix('update')
        _cmd.extend(["-r", str(self.deploy_revision)])
        _cmd.append(settings["vigiconf"].get("confdir"))
        _command = self.createCommand(_cmd)
        try:
            result = _command.execute()
        except SystemCommandError, e:
            raise DispatchatorError(_("Can't execute the request to update the "
                                    "local copy. COMMAND %(cmd)s FAILED. "
                                    "REASON: %(reason)s") % {
                                        'cmd': " ".join(_cmd),
                                        'reason': e.value,
                                   })
        return result


    def _get_auth_svn_cmd_prefix(self, svn_cmd):
        """
        Get an authentified svn command prefix like
        "svn <svn_cmd> --username user --password password "

        @return: the svn command prefix
        @rtype: C{list}
        """
        _cmd = ["svn", svn_cmd]
        svnusername = settings["vigiconf"].get("svnusername", False)
        svnpassword =  settings["vigiconf"].get("svnpassword", False)
        if svnusername and svnpassword:
            _cmd.extend(["--username", svnusername])
            _cmd.extend(["--password", svnpassword])
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
        _cmd = self._get_auth_svn_cmd_prefix('info')
        _cmd.extend(["--xml", "-r", "HEAD"])
        _cmd.append(settings["vigiconf"].get("svnrepository"))
        _command = self.createCommand(_cmd)
        try:
            _command.execute()
        except SystemCommandError, e:
            raise DispatchatorError(_("Can't execute the request to get the "
                                      "current revision: %s") % e.value)

        if not _command.getResult():
            return res
        output = ET.fromstring(_command.getResult(stderr=False))
        entry = output.find("entry")
        if entry is not None:
            res = entry.get("revision", res)
        return int(res)

    def manageReturnQueue(self):
        """
        Manage the data in the return queue. Syslogs all the items.
        @rtype: C{int}
        """
        _result = True # we suppose there is no error (empty queue)
        while not self.returnsQueue.empty(): # syslog each item of the queue
            _result = False
            _error = self.returnsQueue.get()
            LOGGER.error(_error)
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
        if not iServers:
            return
        self.threadedDeployFiles(iServers, iRevision)

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
            raise DispatchatorError(_("The configurations files have not been "
                                        "transfered on every server. See above "
                                        "for more information."))

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
        for _app in self.applications:
            _app.qualifyServers(iServers)

    def deploy(self):
        """
        Does a full deployment: deploy files, qualify files
        """
        _servers = []
        # 1 - build a list of servers that requires deployment
        if self.getModeForce() == False:
            for _srv in self.getServers():
                _srv.updateRevisionManager()
                _srv.getRevisionManager().setSubversion(self.deploy_revision)
                if _srv.needsDeployment():
                    LOGGER.debug(_("Server %s should be deployed."), _srv.getName())
                    _servers.append(_srv)
            if len(_servers) <= 0:
                LOGGER.info(_("All servers are up-to-date. Nothing to do."))
        else: # by default, takes all the servers
            _servers = self.getServers()
        # 2 - deploy on those servers
        self.deploysOnServers(_servers, self.deploy_revision)
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
        _Apps = self.applications
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
            raise DispatchatorError(_("Switch directories was not successful "
                                        "on each server."))

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
        # 1 - build a list of servers that requires restart
        if self.getModeForce() == False:
            for _srv in self.getServers():
                _srv.updateRevisionManager()
                _srv.getRevisionManager().setSubversion(self.deploy_revision)
                if _srv.needsRestart():
                    _servers.append(_srv)
                if _srv.needsDeployment():
                    LOGGER.info(_("Server %s should be deployed."), _srv.getName())
            if len(_servers) <= 0:
                LOGGER.info(_("All servers are up-to-date. No restart needed."))
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
                                        _("Stop applications failed"))

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
                                        _("Start applications failed"))

    def printState(self):
        """Prints a summary"""
        _revision = self.getLastRevision()
        print _("Current revision in the repository : %d") % _revision
        for _srv in self.getServers():
            try:
                _srv.updateRevisionManager()
                _srv.getRevisionManager().setSubversion(_revision)
                _deploymentStr = ""
                _restartStr = ""
                if _srv.needsDeployment():
                    _deploymentStr = _("(should be deployed)")
                if _srv.needsRestart():
                    _restartStr = _("(should restart)")
                print _("Revisions for server %(server)s : %(rev)s%(dep)s%(restart)s") % \
                        {"server": _srv.getName(),
                         "rev": str(_srv.getRevisionManager()),
                         "dep": _deploymentStr, "restart": _restartStr}
            except Exception, e:
                LOGGER.warning(_("Cannot get revision for server: %(server)s. "
                                 "REASON : %(reason)s"),
                                 {"server": _srv.getName(),
                                  "reason": str(e)})

    def run(self, stop_after=None):
        self.prepare_svn()
        if not self.generate():
            return
        if stop_after == "generation":
            return
        self.deploy()
        if stop_after == "deployment":
            return
        self.restart()


# vim:set expandtab tabstop=4 shiftwidth=4:
