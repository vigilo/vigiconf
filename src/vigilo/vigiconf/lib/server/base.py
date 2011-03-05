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
    """Exception involving a L{Server} object"""

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
    A generic Server class
    @ivar name: the hostname
    @type name: C{str}
    """

    def __init__(self, name):
        self.name = name
        self.rev_filename = os.path.join(
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
        Tests wheather the server needs deployment
        @rtype: C{boolean}
        """
        return self.revisions["conf"] != self.revisions["deployed"]

    def needsRestart(self):
        """
        Tests wheather the server needs restarting
        @rtype: C{boolean}
        """
        return self.revisions["deployed"] != self.revisions["installed"]

    # external references
    def getBaseDir(self): # pylint: disable-msg=R0201
        """
        @return: base directory for file deployment
        @rtype: C{str}
        """
        return os.path.join(settings["vigiconf"].get("libdir"), "deploy")

    def createCommand(self, iCommand):
        """
        @note: To be implemented by subclasses
        @param iCommand: command to execute
        @type  iCommand: C{str}
        @return: the command instance
        @rtype: L{SystemCommand<lib.systemcommand.SystemCommand>}
        """
        c = SystemCommand(iCommand)
        c.simulate = self.is_simulation()
        return c

    def is_simulation(self):
        """ get simulation mode.

        @return: simulation or not
        @rtype: C{boolean}
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
        Archive the directory containing the config files

        All the following commands must success or the whole command fails:
         1. test if the DIRECTORY "/tmp/testMV/new" exists
         2. cd into /tmp/testMV
         3. if the DIRECTORY prod exists, rename it to old
         4. rename new to prod
        """
        cmd = ["vigiconf-local", "activate-conf"]
        _command = self.createCommand(cmd)
        try:
            _command.execute()
        except SystemCommandError, e:
            raise ServerError(_("Can't activate the configuration on "
                                "%(server)s. COMMAND %(cmd)s FAILED. "
                                "REASON: %(reason)s") % {
                'server': self.getName(),
                'cmd': cmd,
                'reason': e.value,
            }, self.getName())
        LOGGER.debug("Switched directories on %s", self.name)

    def tarConf(self):
        """
        Tar the configuration files, before deployment
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
        """
        Template function for configuration deployment from the tar archive.
        Must be implemented by a subclass, see L{vigilo.vigiconf.lib.server}.
        """
        raise NotImplementedError

    def deployFiles(self):
        """
        Copy all the configuration files
        """
        self.tarConf()
        self.deployTar()
        LOGGER.info(_("%s : deployement successful."), self.getName())

    def _copy(self, source, destination):
        """
        Simple wrapper around shutil.copyfile.
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
        """Prepare the directory with the validation scripts"""
        validation_dir = self.getValidationDir()
        if not os.path.exists(validation_dir):
            os.makedirs(validation_dir)
        validation_scripts = os.path.join(conf.CODEDIR, "validation", "*.sh")
        for validation_script in glob.glob(validation_scripts):
            shutil.copy(validation_script, validation_dir)

    def deploy(self, rev):
        # update local revision files
        self.revisions["conf"] = rev
        self.revisions["deployed"] = rev
        self.write_revisions()
        # copy the revision file to the deployment directory
        dest_rev_filename = os.path.join(self.getBaseDir(), self.name,
                                         "revisions.txt")
        try:
            os.makedirs(os.path.dirname(dest_rev_filename))
        except OSError:
            pass
        shutil.copyfile(self.rev_filename, dest_rev_filename)
        # insert the "validation" directory in the deployment directory
        self.insertValidationDir()
        # now, the deployment directory is complete.
        self.deployFiles()

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
        Write the SVN revision to our state file
        """
        directory = os.path.dirname(self.rev_filename)
        if not os.path.exists(directory):
            os.makedirs(directory)
        try:
            _file = open(self.rev_filename, 'wb')
            _file.write("Revision: %d" % self.revisions["conf"])
            _file.close()
        except Exception, e: # pylint: disable-msg=W0703
            LOGGER.exception(_("Cannot write the revision file: %s"), e)

    def revisions_summary(self):
        summary = []
        summary.append(_("Deployed: %d") % self.revisions["deployed"])
        summary.append(_("Installed: %d") % self.revisions["installed"])
        summary.append(_("Previous: %d") % self.revisions["previous"])
        return ", ".join(summary)



# vim:set expandtab tabstop=4 shiftwidth=4:
