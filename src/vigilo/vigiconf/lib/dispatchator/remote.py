# -*- coding: utf-8 -*-
################################################################################
#
# VigiConf
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

# pylint: disable-msg=E1101

"""
Ce module contient une sous-classe du L{Dispatchator<base.Dispatchator>} qui
sait gérér des serveurs Vigilo distants.

Ce fichier fait partie de Vigilo Enterprise Edition.
"""

from __future__ import absolute_import

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib.dispatchator.base import Dispatchator


class DispatchatorRemote(Dispatchator):
    """
    Version du Dispatchator qui gère les serveurs distants
    """

    def getServersForApp(self, app):
        """
        Récupère la liste des noms de serveurs pour l'application fournie en
        paramètre.
        @note: Cette méthode doit être réimplémentée par les sous-classes
        @param app: Application à laquelle affecter les serveurs
        @type  app: L{Application<lib.application.Application>}
        @return: Nom des serveurs pour cette application
        @rtype: C{list} de C{str}
        """
        if not app.group:
            # pas de groupe, probablement juste de la génération
            return []
        # If we're not listed in the appsGroupsByServer matrix, bail out
        if not conf.appsGroupsByServer.has_key(app.group):
            LOGGER.warning(_("The %s app group is not listed in "
                             "appsGroupsByServer"), app.group)
            return []
        # Use the appgroup to hostgroup to server mapping
        servers = set()
        for hostgroup in conf.appsGroupsByServer[app.group]:
            for server in conf.appsGroupsByServer[app.group][hostgroup]:
                servers.add(server)
        return list(servers)

    def filter_disabled(self):
        """@see: L{lib.dispatchator.base.Dispatchator.filter_disabled}"""
        servers = self.srv_mgr.filter_servers("is_enabled")
        self.restrict(servers)

    def restrict(self, servernames):
        """
        Limite les serveurs de nos applications aux serveurs fournis en
        paramètre.
        @param servernames: Liste des noms de serveurs
        @type  servernames: C{list} de C{str}
        """
        if not servernames:
            return
        self.srv_mgr.restrict(servernames)
        newapplications = []
        for _app in self.apps_mgr.applications:
            serversforapp = {}
            for _srv in _app.servers:
                if _srv in servernames: # keep it
                    serversforapp[_srv] = _app.servers[_srv]
            if serversforapp: # if there a no server left, just drop the app
                _app.servers = serversforapp
                newapplications.append(_app)
        self.apps_mgr.applications = newapplications

    def server_status(self, servernames, status, no_deploy=False):
        """
        Règle l'état d'un ou plusieurs serveur(s) Vigilo.
        @note: Cette méthode doit être réimplémentée dans les sous-classes
        @param servernames: Les noms des serveurs dont il faut changer l'état
        @type  servernames: C{list} de C{str}
        @param status: Nouvel état à affecter
        @type  status: C{str}
        @param no_deploy: Si C{True}, on ne re-déploiera pas la configuration
        @type  no_deploy: C{bool}
        """
        for servername in servernames:
            server = self.srv_mgr.servers[servername]
            if status == "disable":
                server.disable()
            elif status == "enable":
                server.enable()
        if no_deploy:
            self.commit()
            return
        self.force = True
        self.generate(nosyncdb=True)
        self.prepareServers()
        self.deploy()
        self.commit()
        self.restart()


# vim:set expandtab tabstop=4 shiftwidth=4:
