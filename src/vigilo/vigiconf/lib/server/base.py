# -*- coding: utf-8 -*-
################################################################################
#
# ConfigMgr Data Consistancy dispatchator
# Copyright (C) 2007-2014 CS-SI
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
Ce module contient la classe de base pour un serveur Vigilo: L{Server}.
"""

from __future__ import absolute_import

import os
import shutil
import glob
import re

from vigilo.common.conf import settings

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib import VigiConfError
from vigilo.vigiconf.lib.systemcommand import SystemCommand, SystemCommandError


class ServerError(VigiConfError):
    """Exception concernant un objet L{Server}"""

    def __init__(self, value, iServerName = ''):
        super(ServerError, self).__init__(value)
        self.value = value
        self.mServer = iServerName

    def __str__(self):
        _srvStr = ""
        if( len(self.mServer)>0):
            _srvStr = " on server %s" % (self.mServer)
        return repr("ServerError : %s%s" % (self.value, _srvStr))


class Server(object):
    """
    Un serveur Vigilo.
    @ivar name: nom du serveur (DNS)
    @type name: C{str}
    @ivar revisions: révisions des configurations déployées sur ce serveur.
    @type revisions: C{dict}
    """

    def __init__(self, name):
        self.name = name
        self._rev_filename = os.path.join(
                settings["vigiconf"].get("libdir"),
                "revisions" , "%s.revisions" % name)
        self.revisions = {"conf": None, 
                          "deployed": None,
                          "installed": None,
                          "previous": None,
                          }

    def getName(self):
        """@return: L{name}"""
        return self.name

    def needsDeployment(self):
        """
        Teste si le serveur nécessite un déploiement.
        @rtype: C{bool}
        """
        return self.revisions["conf"] != self.revisions["deployed"]

    def needsRestart(self):
        """
        Teste si le serveur nécessite un redémarrage des applications.
        @rtype: C{bool}
        """
        return self.revisions["deployed"] != self.revisions["installed"]

    def is_enabled(self): # pylint: disable-msg=R0201
        raise NotImplementedError

    # external references
    def getBaseDir(self): # pylint: disable-msg=R0201
        """
        @return: Répertoire de base pour les déploiements.
        @rtype: C{str}
        """
        return os.path.join(settings["vigiconf"].get("libdir"), "deploy")

    def createCommand(self, iCommand):
        """
        @note: À réimplémenter dans les sous-classes.
        @param iCommand: commande à exécuter.
        @type  iCommand: C{str}
        @return: L'instance de la commande
        @rtype: L{SystemCommand<lib.systemcommand.SystemCommand>}
        """
        c = SystemCommand(iCommand)
        c.simulate = self.is_simulation()
        return c

    def is_simulation(self):
        """
        @return: État du mode simulation
        @rtype: C{bool}
        """
        simulate = False
        try:
            simulate = settings["vigiconf"].as_bool("simulate")
        except KeyError:
            pass
        return simulate

    # methods
    def switch_directories(self):
        """
        Archive le répertoire contenant les anciennes configurations, et
        active les nouvelles, à l'aide de C{vigiconf-local}.
        """
        cmd = ["vigiconf-local", "activate-conf"]
        _command = self.createCommand(cmd)
        try:
            _command.execute()
        except SystemCommandError, e:
            raise ServerError(_("Can't activate the configuration on "
                                "%(server)s. COMMAND \"%(cmd)s\" FAILED. "
                                "REASON: %(reason)s") % {
                'server': self.getName(),
                'cmd': " ".join(cmd),
                'reason': e.value,
            }, self.getName())
        LOGGER.debug("Switched directories on %s", self.name)

    def tarConf(self):
        """
        I{Tarre} les fichiers de configuration, avant déploiement.
        """
        cmd = ["tar", "-C",
               os.path.join(self.getBaseDir(), self.getName()), "-cvf",
               os.path.join(self.getBaseDir(), "%s.tar" % self.getName()), "."]
        cmd = SystemCommand(cmd)
        try:
            cmd.execute()
        except SystemCommandError, e:
            raise ServerError(_("Can't tar config for server "
                                "%(server)s: %(error)s") % {
                                    'server': self.getName(),
                                    'error': e.value,
                                })

    def deployTar(self):
        raise NotImplementedError

    def deployFiles(self):
        """
        Copie tous les fichiers de configuration.
        """
        self.tarConf()
        self.deployTar()
        LOGGER.info(_("%s : deployment successful."), self.getName())

    def _copy(self, source, destination):
        """
        Un simple wrapper pour shutil.copyfile.
        @param source: source
        @type  source: C{str}
        @param destination: destination
        @type  destination: C{str}
        """
        try:
            os.makedirs(os.path.dirname(destination))
        except OSError:
            pass
        try:
            shutil.copyfile(source, destination)
        except Exception, e:
            raise ServerError(_("Cannot copy files (%(from)s to %(to)s): "
                                "%(error)s.") % {
                'from': source,
                'to': destination,
                'error': e,
            }, self.getName())

    def getValidationDir(self):
        return os.path.join(self.getBaseDir(), self.getName(), "validation")

    def insertValidationDir(self):
        """
        Prepare le répertoire avec les scripts de validation.
        """
        validation_dir = self.getValidationDir()
        if not os.path.exists(validation_dir):
            os.makedirs(validation_dir)
        validation_scripts = os.path.join(conf.CODEDIR, "validation", "*.sh")
        for validation_script in glob.glob(validation_scripts):
            shutil.copy(validation_script, validation_dir)

    def deploy(self):
        # insert the "validation" directory in the deployment directory
        self.insertValidationDir()
        # now, the deployment directory is complete.
        self.deployFiles()

    def set_revision(self, rev):
        # update local revision files
        self.revisions["conf"] = rev
        self.revisions["deployed"] = rev
        self.write_revisions()
        cmd = self.createCommand(["vigiconf-local", "set-revision", str(rev)])
        cmd.execute()

    def update_revisions(self):
        cmd = self.createCommand(["vigiconf-local", "get-revisions"])
        cmd.execute()
        rev_re = re.compile("^\s*(\w+)\s+(\d+)\s*$")
        revisions = {"new": 0, "prod": 0, "old": 0}
        for line in cmd.getResult().split("\n"):
            rev_match = rev_re.match(line)
            if not rev_match:
                continue
            directory = rev_match.group(1)
            revision = rev_match.group(2)
            revisions[directory] = int(revision)
        self.revisions["deployed"] = revisions["new"]
        self.revisions["installed"] = revisions["prod"]
        self.revisions["previous"] = revisions["old"]

    def write_revisions(self):
        """
        Écrit la révision SVN dans le fichier d'état.
        """
        directory = os.path.dirname(self._rev_filename)
        if not os.path.exists(directory):
            os.makedirs(directory)
        try:
            _file = open(self._rev_filename, 'wb')
            _file.write("Revision: %d\n" % self.revisions["conf"])
            _file.close()
        except Exception, e: # pylint: disable-msg=W0703
            LOGGER.exception(_("Cannot write the revision file: %s"), e)

    def get_state_text(self, last_revision):
        self.update_revisions()
        self.revisions["conf"] = last_revision
        state = ( _("Server %(server)s:\n"
                    "    deployed: %(deployed)d\n"
                    "    installed: %(installed)d\n"
                    "    previous: %(previous)d"
                   )
                  % {"server": self.name,
                     "deployed": self.revisions["deployed"],
                     "installed": self.revisions["installed"],
                     "previous": self.revisions["previous"],
                    } )
        if self.needsDeployment() or self.needsRestart():
            todo = []
            if self.needsDeployment():
                todo.append(_("should be deployed"))
            if self.needsRestart():
                todo.append(_("should restart"))
            state += "\n    -> %s" % ", ".join(todo)
        if not self.is_enabled():
            state += "\n    " + _("disabled").upper()
        return state

    # Disponible dans Vigilo Enterprise Edition
    def disable(self):
        LOGGER.warning(_("Server %s cannot be disabled"), self.name)
    def enable(self):
        LOGGER.warning(_("Server %s cannot be enabled"), self.name)


# vim:set expandtab tabstop=4 shiftwidth=4:
