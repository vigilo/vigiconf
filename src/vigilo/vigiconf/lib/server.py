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

import shutil, os
import socket
import glob

from pkg_resources import working_set

from vigilo.common.conf import settings

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

from vigilo.vigiconf import conf
from . import VigiConfError, EditionError
from .systemcommand import SystemCommand, SystemCommandError
from .revisionmanager import RevisionManager


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


class ServerFactory(object):
    """The Server Factory: returns the right subclass"""

    def __init__(self):
        pass

    def makeServer(self, name):
        """
        Returns the right server object, depending on the hostname
        @param name: the hostname of the Server object to create
        @type  name: C{str}
        @returns: Server object with the provided hostname
        @rtype: L{Server}
        """
        localnames = [ "localhost", socket.gethostname(), socket.getfqdn() ]
        if name in localnames:
            from vigilo.vigiconf.lib.servertypes.local import ServerLocal
            return ServerLocal(name)
        else:
            for entry in working_set.iter_entry_points(
                            "vigilo.vigiconf.extensions", "server_remote"):
                sr_class = entry.load()
                return sr_class(name)
            raise EditionError(_("On the Community Edition, you can only "
                                    "use localhost"), name)


class Server(object):
    """
    A generic Server class
    @ivar name: the hostname
    @type name: C{str}
    @ivar mRevisionManager: the revision manager
    @type mRevisionManager: L{RevisionManager
        <lib.revisionmanager.RevisionManager>}
    """

    def __init__(self, iName):
        self.name = iName
        # mRevisionManager
        self.mRevisionManager = RevisionManager()
        self.mRevisionManager.setRepository(
                settings["vigiconf"].get("svnrepository"))
        self.mRevisionManager.setFilename(os.path.join(
                settings["vigiconf"].get("libdir"),
                "revisions" , iName + ".revisions"))

    def getName(self):
        """@return: L{name}"""
        return self.name

    def getRevisionManager(self):
        """@return: L{mRevisionManager}"""
        return self.mRevisionManager

    def needsDeployment(self):
        """
        Tests wheather the server needs deployment
        @rtype: C{boolean}
        """
        return self.getRevisionManager().isDeployNeeded()

    def needsRestart(self):
        """
        Tests wheather the server needs restarting
        @rtype: C{boolean}
        """
        return self.getRevisionManager().isRestartNeeded()

    # external references
    def getBaseDir(self):
        """
        @return: base directory for file deployment
        @rtype: C{str}
        """
        return os.path.join(settings["vigiconf"].get("libdir"), "deploy")

    def createCommand(self, iCommand, shell=True):
        """
        @note: To be implemented by subclasses
        @param iCommand: command to execute
        @type  iCommand: C{str}
        @return: the command instance
        @rtype: L{SystemCommand<lib.systemcommand.SystemCommand>}
        """
        c = SystemCommand(iCommand, shell=False)
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
    def switchDirectories(self):
        """
        Archive the directory containing the config files

        All the following commands must success or the whole command fails:
         1. test if the DIRECTORY "/tmp/testMV/new" exists
         2. cd into /tmp/testMV
         3. if the DIRECTORY prod exists, rename it to old
         4. rename new to prod
        """
        cmd = "vigiconf-local activate-conf"
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

    def _builddepcmd(self):
        """
        Build the deployment command line
        @note: To be implemented by subclasses.
        """
        return ""

    def tarConf(self):
        """
        Tar the configuration files, before deployment
        """
        cmd = ["tar", "-C",
               os.path.join(self.getBaseDir(), self.getName()), "-cf",
               os.path.join(self.getBaseDir(), "%s.tar" % self.getName()), "."]
        cmd = SystemCommand(cmd)
        try:
            cmd.execute()
        except SystemCommandError, e:
            raise ServerError(_("Can't tar config for server %s: %s")
                               % (self.getName(), e.value))

    def deployTar(self):
        """
        Template function for configuration deployment from the tar archive. Must be implemented by a subclass, see L{vigilo.vigiconf.lib.servertypes}.
        """
        raise NotImplementedError

    def deployFiles(self):
        """
        Copy all the configuration files
        """
        self.tarConf()
        self.deployTar()
        LOGGER.info(_("%s : deployement successful."), self.getName())

    def copy(self, iDestination, iSource):
        """
        Simple wrapper around shutil.copyfile.
        @param iDestination: destination
        @type  iDestination: C{str}
        @param iSource: source
        @type  iSource: C{str}
        @todo: reverse arguments order
        """
        try:
            shutil.copyfile(iSource, iDestination)
        except Exception, e:
            raise ServerError(_("Cannot copy files (%(from)s to %(to)s): "
                                "%(error)s.") % {
                'from': iSource,
                'to': iDestination,
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

    def deploy(self, iRevision):
        """Do the deployment"""
        # update local revision files
        self.getRevisionManager().setSubversion(iRevision)
        self.getRevisionManager().setDeployed(iRevision)
        self.getRevisionManager().writeConfigFile()
        # copy the revisionfile to the deployment directory
        self.copy("%s/%s/revisions.txt" % (self.getBaseDir(), self.getName()),
                  self.getRevisionManager().getFilename())
        # insert the "validation" directory in the deployment directory
        self.insertValidationDir()
        # now, the deployment directory is complete.
        self.deployFiles()

#    def undo(self):
#        """Undo a deployment"""
#        targetdir = settings["vigiconf"].get("targetconfdir")
#        ## check if the directory exists
#        #try:
#        #    _CmdLine = "sh -c '[ -d %s/old ] && [ -d %s/new ]'" \
#        #               % (targetdir, targetdir)
#        #     # execution
#        #    _command = self.createCommand(_CmdLine)
#        #    _command.execute()
#        #    if(_command.integerReturnCode() == 1):
#        #        raise ServerError(_("UNDO can't be done. Directory 'old' "
#        #                            "does not exist on %s.") % self.getName(),
#        #                          self.getName())
#        #except SystemCommandError, e:
#        #    raise ServerError(_("UNDO can't be done. %s") % (str(e)),
#        #                      self.getName())
#        ## undo !
#        try:
#
#            #_newundoStr = "mv %s/new %s/undo" % (targetdir, targetdir)
#            #_oldnew = "mv %s/old %s/new" % (targetdir, targetdir)
#            #_undoold = "mv %s/undo %s/old" % (targetdir, targetdir)
#
#            #_CmdLine = "sudo sh -c ' %s && %s && %s '" \
#            #           % (_newundoStr, _oldnew, _undoold)
#            # execution
#            #_command = self.createCommand(_CmdLine)
#            _command = self.createCommand("vigiconf-local revert-conf")
#            _command.execute()
#            if(_command.integerReturnCode() == 1):
#                raise ServerError(_("UNDO failed on %s.") \
#                                  % (self.getName()), self.getName())
#            else:
#                LOGGER.info(_("UNDO successful on %s."), self.getName())
#        except SystemCommandError, e:
#            raise ServerError(_("UNDO can't be done. %s") % (str(e)),
#                              self.getName())

    # redirections
    def getDeployed(self):
        """
        @return: The deployed SVN revision from the
            L{RevisionManager<lib.revisionmanager.RevisionManager>}
        """
        return self.getRevisionManager().getDeployed()

    def getInstalled(self):
        """
        @return: The installed SVN revision from the
            L{RevisionManager<lib.revisionmanager.RevisionManager>}
        """
        return self.getRevisionManager().getInstalled()

    def getPrevious(self):
        """
        @return: The previous SVN revision from the
            L{RevisionManager<lib.revisionmanager.RevisionManager>}
        """
        return self.getRevisionManager().getPrevious()

    def updateRevisionManager(self):
        """
        Update the SVN revisions in the
        L{RevisionManager<lib.revisionmanager.RevisionManager>}
        """
        self.getRevisionManager().update(self)


# vim:set expandtab tabstop=4 shiftwidth=4:
