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
Ce module contient la classe de base pour le Dispatchator, contrôllant tout le
processus de génération/validation/déploiement des configurations.
"""

from __future__ import absolute_import

import transaction

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)


from vigilo.vigiconf.lib.generators import GenerationError
from vigilo.vigiconf.lib.exceptions import DispatchatorError


class Dispatchator(object):
    """
    Contrôle du processus principal de VigiConf. Une instance de cette classe
    est construite par la factory L{factory.make_dispatchator}().

    @ivar force: Si cette variable est évaluée à C{True}, une synchronisation
        complète de la configuration sera réalisée, et les configurations
        générées seront déployées même si les serveurs ont déjà la bonne
        version de la configuration.
    @type force: C{bool}
    @ivar apps_mgr: Gestionnaire des applications
    @type apps_mgr: L{ApplicationManager<application.ApplicationManager>}
    @ivar rev_mgr: Gestionnaire des révisions de la configuration
    @type rev_mgr: L{RevisionManager<revisionmanager.RevisionManager>}
    @ivar srv_mgr: Gestionnaire des serveurs Vigilo
    @type srv_mgr: L{ServerManager<server.manager.ServerManager>}
    @ivar gen_mgr: Gestionnaire du processus de génération
    @type gen_mgr: L{GeneratorManager<generators.manager.GeneratorManager>}
    """

    def __init__(self, apps_mgr, rev_mgr, srv_mgr, gen_mgr):
        self._force = False # géré comme propriété, voir get_force/set_force
        self.apps_mgr = apps_mgr
        self.rev_mgr = rev_mgr
        self.srv_mgr = srv_mgr
        self.gen_mgr = gen_mgr

    def get_force(self):
        return self._force
    def set_force(self, value):
        self._force = value
        self.rev_mgr.force = value
    force = property(get_force, set_force)

    def restrict(self, servernames):
        """
        Limite les applications et les serveurs à ceux fournis en argument.
        @note: Cette méthode doit être réimplémentée par les sous-classes
        @param servernames: Noms de serveurs
        @type  servernames: C{list} de C{str}
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

    def servers_for_app(self, app):
        raise NotImplementedError()

    def generate(self, nosyncdb=False):
        """
        Génère la configuration des différents composants, en utilisant le
        L{GeneratorManager}.
        @param nosyncdb: Si ce paramètre est C{True}, aucune synchronisation en
            base ne sera réalisée (utile pour redéployer rapidement dans un cas
            de perte d'un serveur Vigilo.
        @type  nosyncdb: C{bool}
        """
        try:
            self.gen_mgr.generate(rev_mgr=self.rev_mgr, nosyncdb=nosyncdb)
        except GenerationError:
            LOGGER.error(_("Generation failed!"))
            raise
        else:
            LOGGER.info(_("Generation successful"))
        # Validation de la génération
        self.apps_mgr.validate()
        # Commit de la configuration dans SVN
        self.rev_mgr.commit()

    def prepareServers(self):
        """
        Prépare la liste des serveurs sur lesquels travailler
        """
        self.filter_disabled()
        if self.force:
            return
        self.srv_mgr.prepare(self.rev_mgr.deploy_revision)

    def deploy(self):
        """
        Déploie et qualifie la configuration sur les serveurs concernés.
        """
        deployed = self.srv_mgr.deploy(self.rev_mgr.deploy_revision,
                                       force=self.force)
        if deployed:
            self.apps_mgr.qualify()

    def commit(self): # pylint: disable-msg=R0201
        """
        Enregistre la configuration en base de données
        """
        try:
            transaction.commit()
            LOGGER.info(_("Database commit successful"))
        except Exception, e:
            transaction.abort()
            LOGGER.debug("Transaction rollbacked: %s", e)
            raise DispatchatorError(_("Database commit failed"))

    def restart(self):
        """
        Redémarre les applications sur les serveurs concernés.
        """
        servers = self.srv_mgr.filter_servers("needsRestart",
                                              force=self.force)
        if not servers:
            LOGGER.info(_("All servers are up-to-date. No restart needed."))
            return
        for server in servers:
            LOGGER.debug("Server %s should be restarted.", server)
        self.apps_mgr.execute("stop", servers)
        self.srv_mgr.switch_directories(servers)
        self.apps_mgr.execute("start", servers)

    def getState(self):
        """
        Retourne un résumé de l'état de la configuration et des serveurs
        Vigilo.
        """
        state = []
        _revision = self.rev_mgr.last_revision()
        state.append(_("Current revision in the repository : %d") % _revision)
        for servername, server in self.servers.items():
            try:
                server.update_revisions()
                server.revisions["conf"] = _revision
                _deploymentStr = ""
                _restartStr = ""
                if server.needsDeployment():
                    _deploymentStr = _("(should be deployed)")
                if server.needsRestart():
                    _restartStr = _("(should restart)")
                state.append(_("Revisions for server %(server)s : "
                               "%(rev)s%(dep)s%(restart)s") % \
                             {"server": servername,
                              "rev": server.revisions_summary(),
                              "dep": _deploymentStr, "restart": _restartStr})
            except Exception, e: # pylint: disable-msg=W0703
                LOGGER.warning(_("Cannot get revision for server: %(server)s. "
                                 "REASON : %(reason)s"),
                                 {"server": servername,
                                  "reason": str(e)})
        return state

    def server_status(self, servernames, status, no_deploy=False):
        raise NotImplementedError()

    def run(self, stop_after=None):
        """
        Méthode principale pour déclencher VigiConf.
        @param stop_after: Étape après laquelle il faut s'arrêter. Valeurs
            possibles : C{generation} ou C{deployment}. Par défaut : on déroule
            la totalité du processus.
        @type  stop_after: C{bool}
        """
        self.rev_mgr.prepare()
        self.generate()
        if stop_after == "generation":
            self.gen_mgr.generate_dbonly()
            return
        self.prepareServers()
        self.deploy()
        if stop_after == "deployment":
            self.gen_mgr.generate_dbonly()
            return
        self.commit()
        self.restart()
        self.gen_mgr.generate_dbonly()


# vim:set expandtab tabstop=4 shiftwidth=4: