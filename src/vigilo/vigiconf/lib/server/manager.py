# -*- coding: utf-8 -*-
# Copyright (C) 2007-2020 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>
"""
Ce module contient la classe de base de L{ServerManager}, permettant de gérer
un parc de serveurs Vigilo.
"""

from __future__ import absolute_import

import Queue
from threading import Thread

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

from vigilo.vigiconf.lib.exceptions import VigiConfError, DispatchatorError


class ServerManager(object):
    """
    Gestionnaire de serveurs Vigilo. Maintient une liste des serveurs
    disponibles, et permet d'effectuer des opérations en masse sur les
    serveurs.

    @ivar servers: C{dict} des serveurs, indexés par le nom (C{str}) et
        pontant sur l'objet (L{Server<base.Server>})
    @type servers: C{dict}
    @ivar factory: instance de L{ServerFactory<factory.ServerFactory>} qui
        servira à construire des objets L{Server<base.Server>} si besoin.
    @type factory: L{ServerFactory<factory.ServerFactory>}
    """

    def __init__(self, factory):
        self.servers = {}
        self.commands_queue = None # will be initialized as Queue.Queue later
        self.returns_queue = None # will be initialized as Queue.Queue later
        self.factory = factory

    def get(self, servername):
        return self.servers[servername]

    def prepare(self, revision):
        for server_obj in self.servers.values():
            server_obj.update_revisions()
            server_obj.revisions["conf"] = revision

    def run_in_thread(self, servers, action, args=None):
        """
        Exécute une action sur des serveurs, en parallèle avec un thread par
        serveur.
        @param servers: Liste de noms de serveurs
        @type  servers: C{list} de C{str}
        @param action: l'action à effectuer, doit correspondre à une méthode de
            L{Server<base.Server>}.
        @type  action: C{str}
        """
        if args is None:
            args = []
        self.commands_queue = Queue.Queue()
        self.returns_queue = Queue.Queue()
        for srv in servers:
            self.commands_queue.put(srv)
            t = Thread(target=self._threaded_action, args=[action, args])
            t.start()
        self.commands_queue.join()
        result = True # we suppose there is no error (empty queue)
        while not self.returns_queue.empty(): # syslog each item of the queue
            result = False
            error = self.returns_queue.get()
            LOGGER.error(error)
        return result

    def _threaded_action(self, action, args):
        """
        Exécute l'action avec les arguments donnés en paramètres. Cette méthode
        est prévue pour s'exécuter dans un thread séparé.
        """
        servername = self.commands_queue.get()
        server = self.servers[servername]
        try:
            getattr(server, action)(*args)
        except VigiConfError as e:
            self.returns_queue.put(e.value)
        self.commands_queue.task_done()

    def filter_servers(self, method, servers=None, force=None):
        if force is None:
            force = ()
        if servers is None:
            servers = self.servers.keys()
        if 'deploy' not in force:
            for server, server_obj in self.servers.items():
                if not getattr(server_obj, method)():
                    servers.remove(server)
        return servers

    def deploy(self, servers=None, force=None):
        """
        Déploie les fichiers de configuration des serveurs, avec un thread par
        serveur.
        @param servers: Liste de noms de serveurs
        @type  servers: C{list} of C{str}
        @return: Liste des serveurs déployés
        @rtype:  C{list}
        """
        if force is None:
            force = ()
        servers = self.filter_servers("needsDeployment", servers, force)
        if not servers:
            LOGGER.info(_("All servers are up-to-date, no deployment needed."))
            return []
        for server in servers:
            LOGGER.debug("Server %s should be deployed.", server)
        result = self.run_in_thread(servers, "deploy")
        if not result:
            raise DispatchatorError(_("The configurations files have not "
                    "been transfered on every server. See above for "
                    "more information."))
        return servers

    def set_revision(self, revision, servers):
        """
        Affecte le numéro de révision dans les fichiers de configuration des
        serveurs, avec un thread par serveur.
        @param revision: Numéro de révision SVN
        @type  revision: C{int}
        @param servers: Liste de noms de serveurs
        @type  servers: C{list} of C{str}
        """
        if not servers:
            return
        result = self.run_in_thread(servers, "set_revision", args=[revision])
        if not result:
            raise DispatchatorError(_("The revision has not "
                    "been set on every server. See above for "
                    "more information."))

    def switch_directories(self, servers=None):
        """
        Permute les répertoires C{prod -> old} et C{new -> prod}, avec un
        thread par serveur.
        @param servers: Liste de noms de serveurs
        @type  servers: C{list} de L{str}
        """
        if servers is None:
            servers = self.servers.keys()
        result = self.run_in_thread(servers, "switch_directories")
        if not result:
            raise DispatchatorError(_("Switch directories was not successful "
                                      "on each server."))



# vim:set expandtab tabstop=4 shiftwidth=4:
