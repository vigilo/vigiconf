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

import os
import Queue
#from optparse import OptionParser
from threading import Thread
import shutil
from xml.etree import ElementTree as ET

from pkg_resources import working_set
import transaction

from vigilo.common.conf import settings
settings.load_module(__name__)

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)


from vigilo.vigiconf import conf
from .generators import GeneratorManager, GenerationError
from .systemcommand import SystemCommand, SystemCommandError
from .application import ApplicationError
from . import VigiConfError


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
    @ivar force: defines if the --force option is set
    @type force: C{boolean}
    @ivar commandsQueue: commands queue
    @type commandsQueue: L{Queue}
    @ivar returnsQueue: commands queue
    @type returnsQueue: L{Queue}
    @ivar deploy_revision: the SVN revision to deploy
    @type deploy_revision: C{str}
    """

    def __init__(self):
        self.applications = []
        self.force = False
        self.commandsQueue = None # will be initialized as Queue.Queue later
        self.returnsQueue = None # will be initialized as Queue.Queue later
        self.deploy_revision = "HEAD"
        self._svn_status = None # cache
        # mode simulation: on recopie simplement la commande svn pour
        # verification
        try:
            self.simulate = settings["vigiconf"].as_bool("simulate")
        except KeyError:
            self.simulate = False
        # initialize applications
        self.listApps()
        self.applications.sort(reverse=True, key=lambda a: a.priority)
        # list servers
        self.servers = self.listServers()

    def restrict(self, servers):
        """
        Restrict applications and servers to the ones given as arguments.
        @note: This method has to be implemented by subclasses
        @param servers: Server names.
        @type  servers: C{list} of C{str}
        """
        pass

    def filter_disabled(self):
        """
        Filtre la liste de serveurs donnée en argument pour ne garder que
        ceux qui ne sont pas marqués comme désactivés en base.
        La liste est changée directement dans la variable, rien n'est
        retourné depuis cette fonction.
        @note: Cette méthode doit être réimplémentée par les sous-classes
        @return: C{None}
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
                msg = _("application %s is not unique.") % app.name
                msg += _(" Providing modules: %s") \
                        % ", ".join(list(working_set.iter_entry_points(
                                "vigilo.vigiconf.applications", entry.name)))
                raise DispatchatorError(msg)
            for server in self.getServersForApp(app):
                app.servers[server] = ["stop", "start"]
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

    def generate(self, generator, nosyncdb=False):
        """
        Génère la configuration des différents composants, en utilisant le
        L{GeneratorManager}.
        """
        try:
            gendir = os.path.join(settings["vigiconf"].get("libdir"), "deploy")
            shutil.rmtree(gendir, ignore_errors=True)
            generator.generate(nosyncdb=nosyncdb)
        except GenerationError:
            LOGGER.error(_("Generation failed!"))
            raise
        else:
            LOGGER.info(_("Generation successful"))
        # Validation de la génération
        self.validate_apps()
        # Commit de la configuration dans SVN
        last_rev = self._svn_commit()
        if self.deploy_revision == "HEAD":
            self.deploy_revision = last_rev
        LOGGER.info(_("SVN commit successful"))


    def validate_apps(self):
        """Validation de la génération"""
        results = []
        for app in self.applications:
            results.append(app.validate_servers(async=True))
        valid = True
        for result in results:
            result_status = result.get()
            valid = valid and result_status
        if not valid:
            raise DispatchatorError(_("validation failed, see above for "
                                      "more information."))
        LOGGER.info(_("Validation successful"))


    def prepare_svn(self):
        """
        Prepare the configuration dir (it's an SVN working directory)
        """
        status = self.get_svn_status()
        if self.deploy_revision != "HEAD" and \
                (status["add"] or status["remove"] or status["modified"]):
            raise DispatchatorError(_("you can't go back to a former "
                "revision if you have modified your configuration. "
                "Use 'svn revert' to cancel your modifications"))
        self._svn_sync(status)

    def get_svn_status(self):
        if self._svn_status is not None:
            return self._svn_status
        _cmd = self._get_auth_svn_cmd_prefix('status')
        _cmd.append("--xml")
        _cmd.append(settings["vigiconf"].get("confdir"))
        _command = self.createCommand(_cmd)
        try:
            _command.execute()
        except SystemCommandError, e:
            raise DispatchatorError(
                    _("can't get the SVN status for the configuration dir: %s")
                      % e.value)
        status = {"toadd": [], "added": [],
                  "toremove": [], "removed": [], 'modified': []}
        if not _command.getResult():
            return status
        output = ET.fromstring(_command.getResult(stderr=False))
        for entry in output.findall(".//entry"):
            state = entry.find("wc-status").get("item")
            if state == "unversioned":
                path = entry.get("path")
                confdir = settings["vigiconf"].get("confdir")
                if path.startswith(os.path.join(confdir, "general")):
                    if not path.endswith(".py"):
                        continue
                else:
                    if not os.path.isdir(path) and not path.endswith(".xml"):
                        continue
                status["toadd"].append(entry.get("path"))
            elif state == "added":
                status["added"].append(entry.get("path"))
            elif state == "missing":
                status["toremove"].append(entry.get("path"))
            elif state == "deleted":
                path = entry.get("path")
                if path.endswith(".xml"):
                    status["removed"].append(path)
                elif os.path.isdir(path):
                    status["removed"].append(path)
                else: # probablement un dossier supprimé avec rm -rf
                    status["toremove"].append(path)
            elif state == "modified":
                status["modified"].append(entry.get("path"))
        return status

    def _svn_sync(self, status=None):
        if not settings["vigiconf"].get("svnrepository", False):
            LOGGER.warning(_("Not updating because the 'svnrepository' "
                               "configuration parameter is empty"))
            return 0
        if status is None:
            status = self.get_svn_status()
        for item in status["toadd"]:
            self._svn_add(item)
        self._svn_update()
        # on applique le remove après le up, sinon le up restaure
        for item in status["toremove"]:
            self._svn_remove(item)
        # Et maintenant on refait un stat pour être sûr (récursivité)
        i = 0
        while status["toadd"] or status["toremove"]:
            status = self.get_svn_status()
            i += 1
            if i > 10: # sécurité
                raise VigiConfError(_("Error while syncing the SVN directory"))
        self._svn_status = status

    def _svn_add(self, path):
        LOGGER.debug("Adding a new configuration file to the "
                     "repository: %s", path)
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
        LOGGER.debug("Removing an old configuration file from the "
                     "repository: %s", path)
        _cmd = self._get_auth_svn_cmd_prefix('remove')
        _cmd.append(path)
        _command = self.createCommand(_cmd)
        try:
            result = _command.execute()
        except SystemCommandError, e:
            if e.returncode == 1 and not os.path.exists(path):
                return # déjà supprimé (probablement un ctrl-c précédent)
            raise DispatchatorError(
                    _("can't remove %(path)s from repository: %(error)s") % {
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
                    _("can't commit the configuration dir in SVN: %s")
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
            raise DispatchatorError(_("can't execute the request to update the "
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
            raise DispatchatorError(_("can't execute the request to get the "
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

    def deploysOnServers(self, iServers, iRevision):
        """
        Deploys the config files to the servers belonging to iServers, using
        one thread per server.
        @param iServers: List of servers
        @type  iServers: C{list} of L{Server<lib.server.Server>}
        @param iRevision: SVN revision number
        @type  iRevision: C{int}
        """
        if not iServers:
            return
        self.commandsQueue = Queue.Queue()
        self.returnsQueue = Queue.Queue()
        for _srv in iServers:
            self.commandsQueue.put(_srv)
            _thread = Thread(target=self.serverDeployFiles, args=[iRevision])
            _thread.start()
        self.commandsQueue.join()
        _result = self.manageReturnQueue()
        if not _result:
            raise DispatchatorError(_("The configurations files have not "
                    "been transfered on every server. See above for "
                    "more information."))

    def serverDeployFiles(self, iRevision):
        """
        Method called by L{deployOnServers} to deploy the files in the
        specified SVN revision
        @param iRevision: SVN revision number
        @type  iRevision: C{int}
        """
        servername = self.commandsQueue.get()
        server = self.servers[servername]
        try:
            server.deploy(iRevision)
        except VigiConfError, e: # if it fails
            self.returnsQueue.put(e.value)
        self.commandsQueue.task_done()

    #  configuration qualification
    def qualify_apps(self, iServers):
        """
        Valide la configuration des applications sur les serveurs distants
        @param iServers: Liste de serveurs
        @type  iServers: C{list} de L{str}
        """
        results = []
        for app in self.applications:
            results.append(app.qualify_servers(async=True))
        valid = True
        for result in results:
            result_status = result.get()
            valid = valid and result_status
        if not valid:
            raise DispatchatorError(_("qualification failed. See above for "
                                      "more information."))
        LOGGER.info(_("Qualification successful"))


    def prepareServers(self):
        """prépare la liste des serveurs sur lesquels travailler"""
        self.filter_disabled()
        if self.force:
            return
        for server_obj in self.servers.values():
            server_obj.updateRevisionManager()
            server_obj.getRevisionManager().setSubversion(self.deploy_revision)

    def deploy(self):
        """
        Déploie et qualifie la configuration sur les serveurs concernés.
        """
        servers = self.servers.keys()
        if not self.force:
            for server, server_obj in self.servers.items():
                if server_obj.needsDeployment():
                    LOGGER.debug("Server %s should be deployed.", server)
                else:
                    servers.remove(server)
        if not servers:
            LOGGER.info(_("All servers are up-to-date, no deployment needed."))
        else:
            self.deploysOnServers(servers, self.deploy_revision)
            self.qualify_apps(servers)

    def commit(self):
        """Enregistre la configuration en base de données"""
        try:
            transaction.commit()
            LOGGER.info(_("Database commit successful"))
        except Exception, e:
            transaction.abort()
            LOGGER.debug("Transaction rollbacked: %s", e)
            raise DispatchatorError(_("Database commit failed"))

    def startOrStopApplications(self, action, servers=None):
        """
        Arrête ou démarre les applications sur les serveurs spécifiés.
        @param action: "start" ou "stop"
        @type  action: C{str}
        """
        if not self.applications:
            return
        if servers is None:
            servers = self.servers.keys()
        status = True
        current_level = self.applications[0].priority
        results = []
        for app in self.applications:
            if (app.priority != current_level):
                # On attend la fin des actions précédentes
                for result in results:
                    result_status = result.get()
                    status = status and result_status
                results = []
                current_level = app.priority
            # exécution de l'action
            results.append(app.execute(action, servers, async=True))
        # on attend les dernières actions
        for result in results:
            result_status = result.get()
            status = status and result_status
        return status

    def switchDirectories(self, servers=None):
        """
        Switch directories prod->old and new->prod, with one thread per server.
        @param iServers: List of servers
        @type  iServers: C{list} of L{str}
        """
        if servers is None:
            servers = self.servers.keys()
        self.commandsQueue = Queue.Queue()
        self.returnsQueue = Queue.Queue()
        for srv in servers:
            self.commandsQueue.put(srv)
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
        servername = self.commandsQueue.get()
        server = self.servers[servername]
        try:
            server.switchDirectories()
        except VigiConfError, e: # if it fails
            self.returnsQueue.put(e.value)
        self.commandsQueue.task_done()
        LOGGER.debug("Switched directories on %s", servername)

    def stopApplications(self, servers=None):
        """
        Stop all the application on the specified servers
        @param servers: List of servers
        @type  servers: C{list} of L{str}
        """
        if servers is None:
            servers = self.servers.keys()
        if not servers:
            return
        self.startOrStopApplications("stop", servers,
                                     _("Stop applications failed"))

    def startApplications(self, servers=None):
        """
        Starts all the application on the servers in iServers
        @param servers: List of servers
        @type  servers: C{list} of L{str}
        """
        if servers is None:
            servers = self.servers.keys()
        if not servers:
            return
        self.startOrStopApplications("start", servers,
                                     _("Start applications failed"))

    def restart(self):
        """
        Redémarre les applications sur les serveurs concernés.
        """
        servers = self.servers.keys()
        if not self.force:
            for server, server_obj in self.servers.items():
                if server_obj.needsRestart():
                    LOGGER.debug("Server %s should be restarted.", server)
                else:
                    servers.remove(server)
        if not servers:
            LOGGER.info(_("All servers are up-to-date. No restart needed."))
        self.startOrStopApplications("stop", servers)
        self.switchDirectories(servers)
        self.startOrStopApplications("start", servers)


    def getState(self):
        """Returns a summary"""
        state = []
        _revision = self.getLastRevision()
        state.append(_("Current revision in the repository : %d") % _revision)
        for servername, server in self.servers.items():
            try:
                server.updateRevisionManager()
                server.getRevisionManager().setSubversion(_revision)
                _deploymentStr = ""
                _restartStr = ""
                if server.needsDeployment():
                    _deploymentStr = _("(should be deployed)")
                if server.needsRestart():
                    _restartStr = _("(should restart)")
                state.append(_("Revisions for server %(server)s : "
                               "%(rev)s%(dep)s%(restart)s") % \
                             {"server": servername,
                              "rev": server.getRevisionManager().getSummary(),
                              "dep": _deploymentStr, "restart": _restartStr})
            except Exception, e:
                LOGGER.warning(_("Cannot get revision for server: %(server)s. "
                                 "REASON : %(reason)s"),
                                 {"server": servername,
                                  "reason": str(e)})
        return state

    def run(self, stop_after=None):
        self.prepare_svn()
        generator = GeneratorManager(self.applications, self)
        self.generate(generator)
        if stop_after == "generation":
            generator.generate_dbonly()
            return
        self.prepareServers()
        self.deploy()
        if stop_after == "deployment":
            generator.generate_dbonly()
            return
        self.commit()
        self.restart()
        generator.generate_dbonly()


# vim:set expandtab tabstop=4 shiftwidth=4:
