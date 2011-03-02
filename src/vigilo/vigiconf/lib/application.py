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
Defines an application that is managed by VigiConf, i.e. Nagios
"""

from __future__ import absolute_import

import os
import Queue
from threading import Thread
# Warning, the "threading" module overwrites the built-in function enumerate()
# if used as import * !!

from pkg_resources import resource_exists, resource_string, working_set

from vigilo.common.conf import settings

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

from vigilo.vigiconf import conf
from .systemcommand import SystemCommand, SystemCommandError
from . import VigiConfError


class ApplicationError(VigiConfError):
    """Exception concerning an application"""

    def __init__(self, *args, **kwargs):
        super(ApplicationError, self).__init__(*args, **kwargs)
        self.cause = None

    def __str__(self):
        return repr("ApplicationError : "+self.value)


class Application(object):
    """
    Une application gérée par VigiConf. La classe fournit des méthodes pour
    démarrer, arrêter et valider l'application.

    @cvar name: nom de l'application
    @type name: C{str}
    @cvar priority: priorité pour l'ordonnancement du redémarrage
    @type priority: C{int}
    @cvar validation: nom d'un script shell pour valider l'application
        localement et à distance. Le nom du script peut être un chemin, mais
        il doit être relatif au package python contenant l'application.
    @type validation: C{str}
    @cvar start_command: commande pour démarrer l'application
    @type start_command: C{str}
    @cvar stop_command: commande pour arrêter l'application
    @type stop_command: C{str}
    @cvar generator: classe utilisée pour la génération, ou None si aucune
        génération n'est nécessaire
    @type generator: instance de L{vigilo.vigiconf.lib.generators.Generator} ou
        C{None}
    @cvar group: groupe logique pour la ventilation
    @type group: C{str}
    @ivar servers: liste des serveurs où l'application est déployée
    @type servers: C{dict}
    """

    name = None
    priority = -1
    validation = None
    start_command = None
    stop_command = None
    generator = None
    group = None
    defaults = {}
    dbonly = False # permet de décaler la génération à la fin du déploiement

    def __init__(self):
        if self.name is None:
            raise NotImplementedError
        self.servers = {}
        self.actions = {}
        self.serversQueue = None # will be initialized as Queue.Queue later
        self.returnsQueue = None # will be initialized as Queue.Queue later


    def __str__(self):
        """
        @return: String representation of the instance
        @rtype: C{str}
        """
        return self.name

    def __repr__(self):
        return "<Application %s>" % self.name

    def getConfig(self):
        config = self.defaults.copy()
        from vigilo.vigiconf import conf
        if self.name in conf.apps_conf:
            config.update(conf.apps_conf[self.name])
        return config

    def generate(self, ventilation):
        generator = self.generator(self, ventilation)
        return generator.generate()

    def filterServers(self, servers):
        """
        @param servers: the list of servers to filter on
        @type  servers: C{list} of C{str}
        @returns: The intersection between servers and our own servers list.
        """
        return set(servers) & set(self.servers) # intersection


    def write_startup_scripts(self, basedir):
        config = self.getConfig()
        for vserver in self.servers:
            scripts_dir = os.path.join(basedir, vserver, "apps", self.name)
            if not os.path.exists(scripts_dir):
                os.makedirs(scripts_dir)
            for action in ["start", "stop"]:
                script_path = os.path.join(scripts_dir, "%s.sh" % action)
                if os.path.exists(script_path):
                    return
                command = self._get_startup_command(action)
                script = open(script_path, "w")
                script.write(command % config)
                script.close()

    def _get_startup_command(self, action):
        command = getattr(self, "%s_command" % action, None)
        if not command: # non déclaré ou vide ou None
            return "#!/bin/sh\nreturn true\n"
        if resource_exists(self.__module__, command):
            # C'est le chemin d'un fichier à utiliser
            return resource_string(self.__module__, command)
        # c'est une commande shell
        return "#!/bin/sh\n%s\n" % command

    def write_validation_script(self, basedir):
        if not self.validation:
            return
        if not resource_exists(self.__module__, self.validation):
            raise ApplicationError(_("Can't find the validation script for "
                                    "app %(app)s: %(error)s") % {
                                        'app': self.name,
                                        'error': self.validation,
                                    })
        for vserver in self.servers:
            scripts_dir = os.path.join(basedir, vserver, "apps", self.name)
            if not os.path.exists(scripts_dir):
                os.makedirs(scripts_dir)
            dest_script = os.path.join(scripts_dir, "validation.sh")
            if os.path.exists(dest_script):
                return
            s = resource_string(self.__module__, self.validation)
            d = open(dest_script, "w")
            d.write(s)
            d.close()

    def validate_servers(self, iServers=None, async=False):
        """
        Validates all the configuration files (starts the validation command)
        @param iBaseDir: The directory where the validation scripts are
        @type  iBaseDir: C{str}
        """
        return self.execute("validate", iServers, async=async)

    def qualify_servers(self, iServers=None, async=False):
        """
        Qualifies the configuration files on the provided servers.
        @param iServers: The servers to qualify on
        @type  iServers: C{list} of C{str}
        """
        return self.execute("qualify", iServers, async=async)

    def start_servers(self, iServers, async=False):
        """
        Start the application on the intersection between iServers and our own
        servers list.
        @param iServers: The servers to start the application on
        @type  iServers: C{list} of C{str}
        """
        return self.execute("start", iServers, async=async)

    def stop_servers(self, iServers, async=False):
        """
        Stop the application on the intersection between iServers and our own
        servers list.
        @param iServers: The servers to stop the application on
        @type  iServers: C{list} of C{str}
        """
        return self.execute("stop", iServers, async=async)

    def execute(self, action, servernames=None, async=False):
        """
        Stop the application on the intersection between iServers and our own
        servers list.
        @param servernames: The servers to act on
        @type  servernames: C{list} of C{str}
        """
        result = True

        self.serversQueue = Queue.Queue()
        self.returnsQueue = Queue.Queue()

        # intersection of serverslists
        if servernames is None:
            servernames = set(self.servers)
        else:
            servernames = self.filterServers(servernames)

        # il faut que l'action courante soit autorisée
        if action in ["stop", "start"]:
            servernames = [ s for s in servernames
                            if action in self.actions[s] ]

        # start the threads
        for servername in servernames:
            self.serversQueue.put(servername)
            _thread = Thread(target=self._threaded_action, args=[action])
            _thread.start()

        result = ActionResult(self.name, action,
                              self.serversQueue, self.returnsQueue)
        if async:
            return result
        else:
            return result.get()

    def _threaded_action(self, action):
        servername = self.serversQueue.get()
        try:
            getattr(self, "%sServer" % action)(servername)
        except ApplicationError, e:
            self.returnsQueue.put(e.value)
        self.serversQueue.task_done()


    def validateServer(self, servername):
        """
        Validates all the configuration files (starts the validation command)
        on the specified server
        @param server: The server to validate on
        @type  server: L{vigilo.vigiconf.lib.server.Server}
        """
        # iterate through the servers
        if not self.validation:
            return
        files_dir = os.path.join(settings["vigiconf"].get("libdir"),
                                 "deploy", servername)
        _command = ["vigiconf-local", "validate-app", self.name, files_dir]
        _command = SystemCommand(_command)
        _command.simulate = settings["vigiconf"].as_bool("simulate")
        try:
            _command.execute()
        except SystemCommandError, e:
            error = ApplicationError(
                        _("%(app)s: validation failed for server "
                          "'%(server)s': %(reason)s")
                        % {"app": self.name,
                           "server": servername,
                           "reason": e})
            error.cause = e
            raise error
        LOGGER.info(_("%(app)s : Validation successful for server: "
                      "%(server)s"),
                    {'app': self.name, 'server': servername})


    def qualifyServer(self, servername):
        """
        qualifies all the configuration files (starts the qualification
        command) on a given server
        @param server: The server to qualify on
        @type  server: L{vigilo.vigiconf.lib.server.Server}
        """
        if not self.validation:
            return
        server = self.servers[servername]
        # A priori pas necessaire, valeur par défaut
        _command = ["vigiconf-local", "validate-app", self.name] #, files_dir]
        _command = server.createCommand(_command)
        try:
            _command.execute()
        except SystemCommandError, e:
            error = ApplicationError(_("%(app)s : Qualification failed on "
                                        "'%(server)s' - REASON: %(reason)s") % {
                                        'app': self.name,
                                        'server': server.name,
                                        'reason':
                                            e.value.decode('utf-8', 'replace'),
                                    })
            error.cause = e
            raise error
        LOGGER.info(_("%(app)s : Qualification successful on server : "
                      "%(server)s"),
                    {'app': self.name, 'server': server.name})


    def startServer(self, servername):
        """
        Starts the application on the specified server
        @param server: The server to start the application on
        @type  server: L{vigilo.vigiconf.lib.server.Server}
        """
        if not self.start_command:
            return
        LOGGER.info(_("Starting %(app)s on %(server)s ..."), {
            'app': self.name,
            'server': servername,
        })
        server = self.servers[servername]
        _command = ["vigiconf-local", "start-app", self.name]
        _command = server.createCommand(_command)
        try:
            _command.execute()
        except SystemCommandError, e:
            error = ApplicationError(_("Can't Start %(app)s on %(server)s "
                                        "- REASON %(reason)s") % {
                'app': self.name,
                'server': server.name,
                'reason': e.value.decode('utf-8', 'replace'),
            })
            error.cause = e
            raise error
        LOGGER.info(_("%(app)s started on %(server)s"), {
            'app': self.name,
            'server': server.name,
        })


    def stopServer(self, servername):
        """
        Stops the application on a given server
        @param server: The server to stop the application on
        @type  server: L{vigilo.vigiconf.lib.server.Server}
        """
        if not self.stop_command:
            return
        LOGGER.info(_("Stopping %(app)s on %(server)s ..."), {
            'app': self.name,
            'server': servername,
        })
        server = self.servers[servername]
        _command = ["vigiconf-local", "stop-app", self.name]
        _command = server.createCommand(_command)
        try:
            _command.execute()
        except SystemCommandError, e:
            error = ApplicationError(_("Can't Stop %(app)s on %(server)s "
                                        "- REASON %(reason)s") % {
                'app': self.name,
                'server': server.name,
                'reason': e.value.decode('utf-8', 'replace'),
            })
            error.cause = e
            raise error
        LOGGER.info(_("%(app)s stopped on %(server)s"), {
            'app': self.name,
            'server': server.name,
        })



class ActionResult(object):

    def __init__(self, app_name, action_name, commands, errors):
        self.app_name = app_name
        self.action_name = action_name
        self._commands = commands
        self._errors = errors

    def process_errors(self):
        """
        Syslogs all the error strings that are in the errors queue
        """
        result = True # we suppose there is no error (empty queue)
        while not self._errors.empty():
            # syslog each item of the queue
            result = False
            error = self._errors.get()
            LOGGER.warning(error)
        return result

    def get(self):
        self._commands.join()
        result = self.process_errors()
        return result
        if not result:
            raise ApplicationError(_("%(app)s: %(action)s process failed.")
                                   % {"app": self.app_name,
                                      "action": self.action_name})
        return True



class ApplicationManager(object):
    def __init__(self):
        self.applications = []

    def list(self):
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
            self.applications.append(app)
        # Vérification : a-t-on déclaré une application non installée ?
        for listed_app in conf.apps:
            if listed_app not in [a.name for a in self.applications]:
                LOGGER.warning(_("Application %s has been added to "
                            "conf.d/general/apps.py, but is not installed")
                            % listed_app)
        self.applications.sort(reverse=True, key=lambda a: a.priority)

    def validate(self):
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

    def qualify(self):
        """
        Valide la configuration des applications sur les serveurs distants
        @param servers: Liste de serveurs
        @type  servers: C{list} de L{str}
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

    def execute(self, action, servers):
        """
        Arrête ou démarre les applications sur les serveurs spécifiés.
        @param action: "start" ou "stop"
        @type  action: C{str}
        """
        if not self.applications:
            return
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



# vim:set expandtab tabstop=4 shiftwidth=4:
