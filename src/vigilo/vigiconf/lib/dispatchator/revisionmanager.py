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
from xml.etree import ElementTree as ET

from vigilo.common.conf import settings
settings.load_module(__name__)

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

from vigilo.vigiconf.lib.systemcommand import SystemCommand, SystemCommandError
from vigilo.vigiconf.lib.exceptions import DispatchatorError


class RevisionManager(object):
    """
    Gestionnaire des révisions et du dossier de travail contenant la
    configuration de VigiConf (conf.d). Actuellement implémenté avec SVN.
    """

    def __init__(self, force=False):
        self._status = None # cache
        self.force = force
        self.deploy_revision = "HEAD"
        self.command_class = SystemCommand

    def prepare(self):
        """
        Prepare the configuration dir (it's an SVN working directory)
        """
        status = self.status()
        if self.deploy_revision != "HEAD" and \
                (status["add"] or status["remove"] or status["modified"]):
            raise DispatchatorError(_("you can't go back to a former "
                "revision if you have modified your configuration. "
                "Use 'svn revert' to cancel your modifications"))
        self.sync()

    def status(self):
        if self._status is not None:
            return self._status
        _cmd = self._get_auth_svn_cmd_prefix('status')
        _cmd.append("--xml")
        _cmd.append(settings["vigiconf"].get("confdir"))
        _command = self.command_class(_cmd)
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
        self._status = status
        return status

    def sync(self, status=None):
        if not settings["vigiconf"].get("svnrepository", False):
            LOGGER.warning(_("Not updating because the 'svnrepository' "
                               "configuration parameter is empty"))
            return 0
        if status is None:
            status = self.status()
        for item in status["toadd"]:
            self.add(item)
        self.update()
        # on applique le remove après le up, sinon le up restaure
        for item in status["toremove"]:
            self.remove(item)
        # Et maintenant on refait un stat pour être sûr (récursivité)
        self._status = None
        i = 0
        while status["toadd"] or status["toremove"]:
            status = self.status()
            i += 1
            if i > 10: # sécurité
                raise DispatchatorError(_("Error while syncing the "
                                          "SVN directory"))

    def add(self, path):
        LOGGER.debug("Adding a new configuration file to the "
                     "repository: %s", path)
        _cmd = ["svn", "add"]
        _cmd.append(path)
        _command = self.command_class(_cmd)
        try:
            result = _command.execute()
        except SystemCommandError, e:
            raise DispatchatorError(
                    _("Can't add %(path)s in repository: %(error)s") % {
                        'path': path,
                        'error': e.value,
                    })
        return result

    def remove(self, path):
        LOGGER.debug("Removing an old configuration file from the "
                     "repository: %s", path)
        _cmd = self._get_auth_svn_cmd_prefix('remove')
        _cmd.append(path)
        _command = self.command_class(_cmd)
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

    def commit(self):
        if not settings["vigiconf"].get("svnrepository", False):
            LOGGER.warning(_("Not committing because the 'svnrepository' "
                           "configuration parameter is empty"))
            return 0
        confdir = settings["vigiconf"].get("confdir")
        _cmd = self._get_auth_svn_cmd_prefix('ci')
        _cmd.extend(["-m", "Auto generate configuration %s" % confdir])
        _cmd.append(confdir)
        _command = self.command_class(_cmd)
        try:
            _command.execute()
        except SystemCommandError, e:
            raise DispatchatorError(
                    _("can't commit the configuration dir in SVN: %s")
                      % e.value)
        last_rev = self.last_revision()
        if self.deploy_revision == "HEAD":
            self.deploy_revision = last_rev
        LOGGER.info(_("SVN commit successful"))
        return last_rev

    def update(self):
        """
        Updates the local copy of the repository
        """
        _cmd = self._get_auth_svn_cmd_prefix('update')
        _cmd.extend(["-r", str(self.deploy_revision)])
        _cmd.append(settings["vigiconf"].get("confdir"))
        _command = self.command_class(_cmd)
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

    def _get_auth_svn_cmd_prefix(self, svn_cmd): # pylint: disable-msg=R0201
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

    def last_revision(self):
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
        _command = self.command_class(_cmd)
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

    def file_changed(self, filename, exclude_added=False,
                     exclude_removed=False):
        if self.force:
            # L'usage de l'option "--force" est considéré comme
            # étant une modification de la configuration.
            return True
        status = self.status()
        changes = status['modified'][:]
        if not exclude_added:
            changes.extend(status["added"])
        if not exclude_removed:
            changes.extend(status["removed"])
        return filename in changes

    def dir_changed(self, dirname):
        if self.force:
            # L'usage de l'option "--force" est considéré comme
            # étant une modification de la configuration.
            return True
        status = self.status()
        changes = status['added'] + \
                  status['removed'] + \
                  status['modified']
        for changed in changes:
            if changed.startswith(dirname):
                return True

    def get_removed(self):
        status = self.status()
        return status["removed"]



# vim:set expandtab tabstop=4 shiftwidth=4:
