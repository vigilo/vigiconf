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
Describes a Server to push and commit new software configurations to
"""

from __future__ import absolute_import

import os
import shutil
import socket
import glob
import re
import Queue
from threading import Thread

from pkg_resources import working_set

from vigilo.common.conf import settings

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib.exceptions import VigiConfError, DispatchatorError


class ServerManager(object):

    def __init__(self, factory):
        self.servers = []
        self.commands_queue = None # will be initialized as Queue.Queue later
        self.returns_queue = None # will be initialized as Queue.Queue later
        self.factory = factory

    def get(self, servername):
        return self.servers[servername]

    def prepare(self, revision):
        for server_obj in self.servers.values():
            server_obj.update_revisions()
            server_obj.revisions["conf"] = revision

    def run_in_thread(self, servers, action, args=[]):
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
        servername = self.commands_queue.get()
        server = self.servers[servername]
        try:
            getattr(server, action)(*args)
        except VigiConfError, e: # if it fails
            self.returns_queue.put(e.value)
        self.commands_queue.task_done()

    def filter_servers(self, method, servers=None, force=False):
        if servers is None:
            servers = self.servers.keys()
        if not force:
            for server, server_obj in self.servers.items():
                if not getattr(server_obj, method)():
                    servers.remove(server)
        return servers

    def deploy(self, revision, servers=None, force=False):
        """
        Deploys the config files to the servers belonging to iServers, using
        one thread per server.
        @param iServers: List of servers
        @type  iServers: C{list} of L{Server<lib.server.Server>}
        @param iRevision: SVN revision number
        @type  iRevision: C{int}
        @return: number of servers deployed
        @rtype:  C{int}
        """
        servers = self.filter_servers("needsDeployment", servers, force)
        if not servers:
            LOGGER.info(_("All servers are up-to-date, no deployment needed."))
            return 0
        for server in servers:
            LOGGER.debug("Server %s should be deployed.", server)
        result = self.run_in_thread(servers, "deploy", args=[revision])
        if not result:
            raise DispatchatorError(_("The configurations files have not "
                    "been transfered on every server. See above for "
                    "more information."))
        return len(servers)

    def switch_directories(self, servers=None):
        """
        Switch directories prod->old and new->prod, with one thread per server.
        @param servers: List of servers
        @type  servers: C{list} of L{str}
        """
        if servers is None:
            servers = self.servers.keys()
        result = self.run_in_thread(servers, "switch_directories")
        if not result:
            raise DispatchatorError(_("Switch directories was not successful "
                                      "on each server."))



# vim:set expandtab tabstop=4 shiftwidth=4:
