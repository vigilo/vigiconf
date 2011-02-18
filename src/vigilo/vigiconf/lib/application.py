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
import threading
# Warning, the "threading" module overwrites the built-in function enumerate()
# if used as import * !!

from pkg_resources import resource_exists, resource_string

from vigilo.common.conf import settings

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

from .systemcommand import SystemCommand, SystemCommandError
from . import VigiConfError
from .server import serverfactory


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
    @type servers: C{list} de C{str}
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

    def filterServers(self, servers):
        """
        @param servers: the list of servers to filter on
        @type  servers: C{list} of C{str}
        @returns: The intersection between servers and our own servers list.
        """
        return set(servers) & set(self.servers) # intersection

    def manageReturnQueue(self):
        """
        Syslogs all the error strings that are in the return queue
        """
        _result = True # we suppose there is no error (empty queue)
        while not self.returnsQueue.empty(): # syslog each item of the queue
            _result = False
            _error = self.returnsQueue.get()
            LOGGER.warning(_error)
        return _result


    def validate(self, iBaseDir):
        """
        Validates all the configuration files (starts the validation command)
        @param iBaseDir: The directory where the validation scripts are
        @type  iBaseDir: C{str}
        """
        # iterate through the servers
        for server in self.servers:
            try:
                self.validateServer(iBaseDir, server)
            except ApplicationError:
                raise

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

    def validateServer(self, iBaseDir, iServer):
        """
        Validates all the configuration files (starts the validation command)
        on the specified server
        @param iBaseDir: The directory where the validation scripts are
        @type  iBaseDir: C{str}
        @param iServer: The server to validate on
        @type  iServer: C{str}
        """
        # iterate through the servers
        if not self.validation:
            return
        files_dir = os.path.join(iBaseDir, iServer)
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
                           "server": iServer,
                           "reason": e})
            error.cause = e
            raise error
        LOGGER.info(_("%(app)s : Validation successful for server: "
                      "%(server)s"),
                    {'app': self.name, 'server': iServer})


    def qualify(self):
        """
        Qualifies all the configuration files (starts the qualification command
        on each server)
        """
        # iterate through the servers
        for server in self.servers:
            try:
                self.qualifyServer(server)
            except ApplicationError:
                raise

    def qualifyServers(self, iServers):
        """
        Qualifies the configuration files on the provided servers.
        @param iServers: The servers to qualify on
        @type  iServers: C{list} of C{str}
        """
        for _srv in self.filterServers(iServers):
            # can be threaded 1 thread per server
            self.qualifyServer(_srv)



    def qualifyServer(self, iServer):
        """
        qualifies all the configuration files (starts the qualification
        command) on a given server
        @param iServer: The server to qualify on
        @type  iServer: C{str}
        """
        if not self.validation:
            return
        server_obj = serverfactory.makeServer(iServer)
        # A priori pas necessaire, valeur par défaut
        _command = ["vigiconf-local", "validate-app", self.name] #, files_dir]
        _command = server_obj.createCommand(_command)
        try:
            _command.execute()
        except SystemCommandError, e:
            error = ApplicationError(_("%(app)s : Qualification failed on "
                                        "'%(server)s' - REASON: %(reason)s") % {
                                        'app': self.name,
                                        'server': iServer,
                                        'reason':
                                            e.value.decode('utf-8', 'replace'),
                                    })
            error.cause = e
            raise error
        LOGGER.info(_("%(app)s : Qualification successful on server : "
                      "%(server)s"),
                    {'app': self.name, 'server': iServer})


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
        @type  iServers: C{list} of C{str}
        """
        result = True

        self.serversQueue = Queue.Queue()
        self.returnsQueue = Queue.Queue()

        # intersection of serverslists
        _servers = self.filterServers(iServers)
        for _server in _servers:
            # fill the application queue
            if self.servers[_server] == "stop":
                continue
            self.serversQueue.put(_server)

        # start the threads
        for _server in _servers:
            if self.servers[_server] == "stop":
                continue
            _thread = threading.Thread(target = self.startThread)
            _thread.start()

        # wait until the queue is empty
        self.serversQueue.join()

        result = self.manageReturnQueue()
        if result == False:
            raise ApplicationError(_("%s : Start process failed.")
                                   % (self.name))

    def start(self):
        """Starts the application"""
        result = True

        self.serversQueue = Queue.Queue()
        self.returnsQueue = Queue.Queue()

        for _server in self.servers:
            # fill the application queue
            self.serversQueue.put(_server)

        # start the threads
        for _server in self.servers:
            _thread = threading.Thread(target = self.startThread)
            _thread.start()

        # wait until the queue is empty
        self.serversQueue.join()

        result = self.manageReturnQueue()
        if result == False:
            raise ApplicationError(_("%s : Start process failed.")
                                   % (self.name))


    def startServer(self, iServer):
        """
        Starts the application on the specified server
        @param iServer: The server to start the application on
        @type  iServer: C{str}
        """
        if not self.start_command:
            return
        LOGGER.info(_("Starting %(app)s on %(server)s ..."), {
            'app': self.name,
            'server': iServer,
        })
        server_obj = serverfactory.makeServer(iServer)
        _command = ["vigiconf-local", "start-app", self.name]
        _command = server_obj.createCommand(_command)
        try:
            _command.execute()
        except SystemCommandError, e:
            error = ApplicationError(_("Can't Start %(app)s on %(server)s "
                                        "- REASON %(reason)s") % {
                'app': self.name,
                'server': iServer,
                'reason': e.value.decode('utf-8', 'replace'),
            })
            error.cause = e
            raise error
        LOGGER.info(_("%(app)s started on %(server)s"), {
            'app': self.name,
            'server': iServer,
        })

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
        @type  iServers: C{list} of C{str}
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
            raise ApplicationError(_("%s : Stop process failed.")
                                   % (self.name))

    def stop(self):
        """Stops the applications"""
        result = True

        self.serversQueue = Queue.Queue()
        self.returnsQueue = Queue.Queue()

        for _server in self.servers:
            # fill the application queue
            self.serversQueue.put(_server)

        # start the threads
        for _server in self.servers:
            _thread = threading.Thread(target = self.stopThread)
            _thread.start()

        # wait until the queue is empty
        self.serversQueue.join()

        result = self.manageReturnQueue()
        if result == False :
            raise ApplicationError(_("%s : Stop process failed.")
                                   % (self.name))


    def stopServer(self, iServer):
        """
        Stops the application on a given server
        @param iServer: The server to stop the application on
        @type  iServer: C{str}
        """
        if not self.stop_command:
            return
        LOGGER.info(_("Stopping %(app)s on %(server)s ..."), {
            'app': self.name,
            'server': iServer,
        })
        server_obj = serverfactory.makeServer(iServer)
        _command = ["vigiconf-local", "stop-app", self.name]
        _command = server_obj.createCommand(_command)
        try:
            _command.execute()
        except SystemCommandError, e:
            error = ApplicationError(_("Can't Stop %(app)s on %(server)s "
                                        "- REASON %(reason)s") % {
                'app': self.name,
                'server': iServer,
                'reason': e.value,
            })
            error.cause = e
            raise error
        LOGGER.info(_("%(app)s stopped on %(server)s"), {
            'app': self.name,
            'server': iServer,
        })


# vim:set expandtab tabstop=4 shiftwidth=4:
