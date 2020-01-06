# -*- coding: utf-8 -*-
# Copyright (C) 2007-2020 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Ce module contient L{RevisionManager}, une classe permettant de contrôller
le système de gestion de version qui gère les révisions de la configuration.
"""

from __future__ import absolute_import

import os
import itertools
from xml.etree import ElementTree as ET

from vigilo.common.conf import settings
settings.load_module(__name__)

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

from vigilo.models.session import DBSession
from vigilo.models.tables import Version

from vigilo.vigiconf.lib.systemcommand import SystemCommand, SystemCommandError
from vigilo.vigiconf.lib.exceptions import DispatchatorError


class RevisionManager(object):
    """
    Gestionnaire des révisions et du dossier de travail contenant la
    configuration de VigiConf (C{conf.d}). Actuellement implémenté avec
    Subversion.
    """
    version_key = u'vigiconf.configuration'

    def __init__(self, author=None, message=None, force=None):
        if force is None:
            force = ()
        self._status = None # cache
        self.force = force
        self.deploy_revision = "HEAD"
        self.command_class = SystemCommand
        self.commit_author = author
        self.commit_message = message

    def prepare(self):
        """
        Prepare le dossier de configuration (c'est une copie de travail SVN).
        """
        status = self.sync()
        if self.deploy_revision != "HEAD" and \
                (status["add"] or status["remove"] or status["modified"]):
            raise DispatchatorError(_("you can't go back to a former "
                "revision if you have modified your configuration. "
                "Use 'svn revert' to cancel your modifications"))
        last_rev = self.commit()
        self.status()
        if last_rev == 1:
            self.force = self.force + ("db-sync", )

    def status(self):
        """
        Retourne le résultat de la commande C{svn status} dans un
        dictionnaire indexé par état et listant les fichiers.
        @rtype:  C{dict}
        """
        if self._status is not None:
            return self._status

        old_rev = Version.by_object_name(self.version_key)
        if old_rev is None:
            old_rev = 0
        else:
            old_rev = old_rev.version

        new_rev = self.last_revision()
        confdir = settings["vigiconf"].get("confdir")
        _cmd = [
            "svn", "diff", "--xml", "--summarize",
            "-r", "%d:%d" % (old_rev, new_rev),
            confdir,
        ]
        LOGGER.debug('Running this command: %s' % ' '.join(_cmd))
        _command = self.command_class(_cmd)
        try:
            _command.execute()
        except SystemCommandError as e:
            raise DispatchatorError(
                _("can't compute SVN differences "
                  "for the configuration dir: %s")
                  % e.value)
        status = {"added": [], "removed": [], 'modified': []}
        if not _command.getResult():
            return status

        removed = []
        output = ET.fromstring(_command.getResult(stderr=False))
        for entry in output.findall(".//path"):
            change = entry.get("item")
            if change == "deleted":
                removed.append(entry.text)
            else:
                status[change].append(entry.text)
        status['removed'] = [e for e in removed
                             if os.path.dirname(e) not in removed]
        self._status = status
        return status

    def sync(self):
        """
        Synchronise l'état SVN avec l'état réel du dossier. Exécute un
        C{svn add} sur les fichiers ou dossiers ajoutés, et un
        C{svn remove} sur ce qui a été supprimé.
        """
        if not settings["vigiconf"].get("svnrepository", False):
            LOGGER.warning(_("Not updating because the 'svnrepository' "
                               "configuration parameter is empty"))
            return {}

        confdir = settings["vigiconf"].get("confdir")
        _cmd = ["svn", "status", "--xml", confdir]
        _command = self.command_class(_cmd)
        try:
            _command.execute()
        except SystemCommandError as e:
            raise DispatchatorError(
                _("can't get SVN status for the configuration dir: %s")
                  % e.value)

        status = {"toadd": [], "added": [],
                  "toremove": [], "removed": [], 'modified': []}
        removed_dirs = []
        if _command.getResult():
            output = ET.fromstring(_command.getResult(stderr=False))
            for entry in output.findall(".//entry"):
                state = entry.find("wc-status").get("item")
                if state == "unversioned":
                    path = entry.get("path")
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
                    # FIXME: lors d'une suppression manuelle de dossier
                    # sous subversion 1.7.x, svn renvoit désormais la liste
                    # des fichiers comme faisant partie de la suppression.
                    #
                    # On élimine ces fichiers (inattendus par VigiConf)
                    # de la liste, pour rester compatible avec svn 1.6.
                    # On s'appuie pour cela sur le fait que la liste
                    # retournée par svn est triée (parents puis enfants).
                    #
                    # Idéalement, il ne faudrait plus supporter svn 1.6.
                    path = entry.get("path")
                    if os.path.dirname(path) not in removed_dirs:
                        status["toremove"].append(path)
                    removed_dirs.append(path)
                elif state == "deleted":
                    status["removed"].append(entry.get("path"))
                elif state == "modified":
                    status["modified"].append(entry.get("path"))

        # Le up permet de restaurer les fichiers afin de pouvoir
        # les supprimer correctement ensuite.
        self.update()
        for item in status["toadd"]:
            self.add(item)
        for item in status["toremove"]:
            self.remove(item)
        return status

    def add(self, path):
        """
        Exécute un C{svn add} sur le chemin spécifié.
        @param path: Chemin à ajouter.
        @type  path: C{str}
        """
        LOGGER.debug("Adding a new configuration file to the "
                     "repository: %s", path)
        _cmd = ["svn", "add", path]
        _command = self.command_class(_cmd)
        try:
            result = _command.execute()
        except SystemCommandError as e:
            raise DispatchatorError(
                    _("Can't add %(path)s in repository: %(error)s") % {
                        'path': path,
                        'error': e.value,
                    })
        return result

    def remove(self, path):
        """
        Exécute un C{svn remove} sur le chemin spécifié.
        @param path: Chemin à supprimer.
        @type  path: C{str}
        """
        LOGGER.debug("Removing an old configuration file from the "
                     "repository: %s", path)
        #_cmd = self._get_auth_svn_cmd_prefix('remove')
        _cmd = ["svn", "remove", path]
        _command = self.command_class(_cmd)
        try:
            result = _command.execute()
        except SystemCommandError as e:
            if e.returncode == 1 and not os.path.exists(path):
                return # déjà supprimé (probablement un ctrl-c précédent)
            raise DispatchatorError(
                    _("can't remove %(path)s from repository: %(error)s") % {
                        'path': path,
                        'error': e.value,
                    })
        return result

    def commit(self):
        """
        Exécute un C{svn commit} dans le dossier de configuration.
        """
        if not settings["vigiconf"].get("svnrepository", False):
            LOGGER.warning(_("Not committing because the 'svnrepository' "
                           "configuration parameter is empty"))
            return 0
        confdir = settings["vigiconf"].get("confdir")
        _cmd = self._get_auth_svn_cmd_prefix('ci')
        if self.commit_message:
            _cmd.extend(["-m", "%s committed: %s" %
                                (self.commit_author, self.commit_message)])
        else:
            _cmd.extend(["-m", "Auto-generated from %s on behalf of %s" %
                                (confdir, self.commit_author)])
        _cmd.append(confdir)
        _command = self.command_class(_cmd)
        try:
            _command.execute()
        except SystemCommandError as e:
            raise DispatchatorError(
                    _("can't commit the configuration dir in SVN: %s")
                      % e.value)
        last_rev = self.last_revision()
        if self.deploy_revision == "HEAD":
            self.deploy_revision = last_rev
        LOGGER.info(_("SVN commit successful"))
        return last_rev

    def db_commit(self):
        version_obj = Version.by_object_name(self.version_key)
        if version_obj is None:
            version_obj = Version(name=self.version_key)
        if self.deploy_revision == "HEAD":
            self.deploy_revision = self.last_revision()
        version_obj.version = self.deploy_revision
        DBSession.add(version_obj)
        DBSession.flush()


    def update(self):
        """
        Exécute un C{svn update} dans le dossier de configuration.
        """
        _cmd = self._get_auth_svn_cmd_prefix('update')
        _cmd.extend(["-r", str(self.deploy_revision)])
        _cmd.append(settings["vigiconf"].get("confdir"))
        _command = self.command_class(_cmd)
        try:
            result = _command.execute()
        except SystemCommandError as e:
            raise DispatchatorError(_("can't execute the request to update the "
                                    "local copy. COMMAND %(cmd)s FAILED. "
                                    "REASON: %(reason)s") % {
                                        'cmd': " ".join(_cmd),
                                        'reason': e.value,
                                   })
        return result

    def _get_auth_svn_cmd_prefix(self, svn_cmd): # pylint: disable-msg=R0201
        """
        Retourne un début de commande SVN incluant l'authentification
        paramétrée dans le fichier C{settings.ini}.
        @return: Le début de la commande SVN
        @rtype: C{list}
        """
        _cmd = ["svn", svn_cmd]
        svnusername = settings["vigiconf"].get("svnusername", False)
        svnpassword =  settings["vigiconf"].get("svnpassword", False)
        if svnusername and svnpassword:
            _cmd.extend(["--username", svnusername])
            _cmd.extend(["--password", svnpassword])
        return _cmd

    def last_revision(self):
        """
        Retourne la dernière révision des fichiers en exécutant un
        C{svn info} dans le dossier de configuration.
        @return: Le numéro de la dernière révision
        @rtype: C{int}
        """
        res = 0
        if not settings["vigiconf"].get("svnrepository", False):
            return res
        _cmd = self._get_auth_svn_cmd_prefix('info')
        _cmd.extend(["--xml", "-r", "HEAD"])
        _cmd.append(settings["vigiconf"].get("svnrepository"))
        _command = self.command_class(_cmd)
        try:
            _command.execute()
        except SystemCommandError as e:
            raise DispatchatorError(_("can't execute the request to get the "
                                      "current revision: %s") % e.value)

        if not _command.getResult():
            return res
        output = ET.fromstring(_command.getResult(stderr=False))
        entry = output.find("entry")
        if entry is not None:
            res = entry.get("revision", res)
        return int(res)

    def file_changed(self, filename, exclude_added=False,
                     exclude_removed=False):
        """
        Retourne l'état de modification d'un fichier.
        @param filename: Fichier à analyser
        @type  filename: C{str}
        @param exclude_added: Si C{True}, ne considère pas les fichiers
            ajoutés.
        @type  exclude_added: C{bool}
        @param exclude_removed: Si C{True}, ne considère pas les fichiers
            supprimés.
        @type  exclude_removed: C{bool}
        @return: C{True} si C{filename} a été modifiée, C{False} sinon.
        @rtype: C{bool}
        """
        if "db-sync" in self.force:
            # L'option "--force db-sync" est traitée comme s'il
            # s'agissait d'une modification de la configuration.
            return True
        status = self.status()
        confdir = settings["vigiconf"].get("confdir")
        # Suppression des séparateurs de dossiers ('/') en fin de valeur.
        while confdir.endswith(os.path.sep):
            confdir = confdir[:-len(os.path.sep)]
        while filename != confdir:
            if filename in status['modified']:
                return True
            if (not exclude_added) and filename in status["added"]:
                return True
            if (not exclude_removed) and filename in status["removed"]:
                return True
            # L'élément courant n'a pas été modifié/ajouté/supprimé,
            # on réitère en testant son dossier parent.
            new_filename = filename.rpartition(os.path.sep)[0]
            # Protection contre les boucles infinies.
            if new_filename == filename:
                break
            filename = new_filename
        return False

    def _is_in_dir(self, dirname, filename):
        """
        Permet de savoir si un fichier appartient à un dossier.
        @param dirname: Dossier à analyser.
        @type  dirname: C{str}
        @param filename: Fichier (ou dossier) à analyser.
        @type  filename: C{str}
        @return: C{True} si C{filename} est un sous élément de C{dirname},
                 C{False} sinon.
        @rtype: C{bool}
        """
        f = os.path.normpath(filename)
        d = os.path.normpath(dirname)
        prefix = os.path.commonprefix([f, d])
        if prefix == d:
            # Il y a un préfixe commun, il faut des vérifications
            # supplémentaires.
            suffix = f.replace(prefix, '').lstrip(os.path.sep)
            prefix_sep_suffix = os.path.join(prefix, suffix)
            if prefix_sep_suffix == f or prefix_sep_suffix == f + os.path.sep:
                return True
        return False

    def dir_changed(self, dirname):
        """
        Retourne l'état de modification d'un dossier.
        @param dirname: Dossier à analyser
        @type  dirname: C{str}
        @return: C{True} si C{dirname} a été modifié ou un sous élément de
                 C{dirname}, C{False} sinon.
        @rtype: C{bool}
        """
        if "db-sync" in self.force:
            # L'option "--force db-sync" est traitée comme s'il
            # s'agissait d'une modification de la configuration.
            return True
        status = self.status()
        added = iter(status['added'])
        modified = iter(status['modified'])
        removed = iter(status['removed'])
        for filename in itertools.chain(added, modified, removed):
            if self._is_in_dir(dirname, filename):
                return True
        return False

    def get_removed(self):
        """
        Retourne la liste des fichiers ou dossiers supprimés.
        @rtype: C{list}
        """
        status = self.status()
        return status["removed"][:]


# vim:set expandtab tabstop=4 shiftwidth=4:
