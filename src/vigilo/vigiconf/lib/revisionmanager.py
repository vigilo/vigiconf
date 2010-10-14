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
Handles the revisions deployed, running, planned on the ConfMgr system
"""

from __future__ import absolute_import

import os
import re
import locale

from vigilo.common.conf import settings

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

from .. import conf
from . import VigiConfError


class RevisionManagerError(VigiConfError):
    """The exception type raised by instances of RevisionManager"""

    def __str__(self):
        """
        @returns: A representation of an instance of RevisionManagerError
        @rtype: C{str}
        """
        return repr("RevisionManagerError : "+self.value)


class RevisionManager(object):
    """
    Manage all SVN revision parameters.

    @ivar mFilename: a filename to store the revisions
    @type mFilename: C{str}
    @ivar mRepository: The URL to the SVN repository
    @type mRepository: C{str}
    @ivar mSubversion: The revision commited to the SVN server on startup
    @type mSubversion: C{int}
    @ivar mDeployed: The revision that is currently deployed
    @type mDeployed: C{int}
    @ivar mInstalled: The revision that is currently installed
    @type mInstalled: C{int}
    @ivar mPrevious: The revision that has been installed last time
    @type mPrevious: C{int}
    """

    def __init__(self):
        self.mFilename = ""
        self.mRepository = ""
        self.mSubversion = 0
        self.mDeployed = 0
        self.mInstalled = 0
        self.mPrevious = 0
        #self.readPickle()

    def __str__(self):
        _str = "Revision<"
        #_str += "Pickle : %s\n"%(self.mFilename)
        #_str += "SVN : %d\n"%(self.getSubversion())
        _str += "DEP : %d, " % (self.getDeployed())
        _str += "INS : %d, " % (self.getInstalled())
        _str += "PRE : %d>" % (self.getPrevious())
        return _str

    def getRepository(self):
        """@return: L{mRepository}"""
        return self.mRepository

    def getSubversion(self):
        """@return: L{mSubversion}"""
        return self.mSubversion

    def getDeployed(self):
        """@return: L{mDeployed}"""
        return self.mDeployed

    def getInstalled(self):
        """@return: L{mInstalled}"""
        return self.mInstalled

    def getPrevious(self):
        """@return: L{mPrevious}"""
        return self.mPrevious

    def getFilename(self):
        """@return: L{mFilename}"""
        return self.mFilename

    def setSubversion(self, iRevision):
        """
        Sets L{mSubversion}.
        @param iRevision: an SVN revision
        @type  iRevision: C{int}
        """
        self.mSubversion = iRevision

    def setDeployed(self, iRevision):
        """
        Sets L{mDeployed}.
        @param iRevision: an SVN revision
        @type  iRevision: C{int}
        """
        self.mDeployed = iRevision

    def setInstalled(self, iRevision):
        """
        Sets L{mInstalled}.
        @param iRevision: an SVN revision
        @type  iRevision: C{int}
        """
        self.mInstalled = iRevision

    def setPrevious(self, iRevision):
        """
        Sets L{mPrevious}.
        @param iRevision: an SVN revision
        @type  iRevision: C{int}
        """
        self.mPrevious = iRevision

    def setFilename(self, iFilename):
        """
        Sets L{mFilename}.
        @param iFilename: a filename
        @type  iFilename: C{str}
        """
        self.mFilename = iFilename

    def setRepository(self, iRepository):
        """
        Sets L{mRepository}.
        @param iRepository: an SVN repository URL
        @type  iRepository: C{str}
        """
        self.mRepository = iRepository

    def writeConfigFile(self):
        """
        Write the SVN revision to our state file
        """
        directory = os.path.dirname(self.getFilename())
        if not os.path.exists(directory):
            os.makedirs(directory)
        try:
            _file = open(self.getFilename(), 'wb')
            _file.write("Revision: %d"%(self.getSubversion()))
            _file.close()
        except Exception, e:
            LOGGER.exception(_("Cannot write the revision file: %s"), e)

    def isDeployNeeded(self):
        """
        Test wheather a deployment is needed
        @rtype: C{boolean}
        """
        return (self.getSubversion() != self.getDeployed())

    def isRestartNeeded(self):
        """
        Test wheather a restart is needed
        @rtype: C{boolean}
        """
        return (self.getDeployed() != self.getInstalled())

## remote gets

    def getRevisions(self, iServer):
        """
        Returns the revision values contained in the file named iFilename on the
        server iServer. If the file does not exist then 0 is returned (ie:
        first deployment)
        @param iServer: The server to contact
        @type  iServer: L{Server<lib.server.Server>}
        @returns: The SVN revisions
        @rtype: C{dict}
        """
        cmd = iServer.createCommand(["vigiconf-local", "get-revisions"])
        cmd.execute()
        rev_re = re.compile("^\s*(\w+)\s+(\d+)\s*$")
        revisions = {"new": 0, "prod": 0, "old": 0,}
        for line in cmd.getResult().split("\n"):
            rev_match = rev_re.match(line)
            if not rev_match:
                continue
            directory = rev_match.group(1)
            revision = rev_match.group(2)
            revisions[directory] = int(revision)
        return revisions

    def update(self, iServer):
        """
        Updates the SVN revision values by getting the new values in the
        appropriate files on the server iServer
        @param iServer: The server to update
        @type  iServer: L{Server<lib.server.Server>}
        """
        revisions = self.getRevisions(iServer)
        self.setDeployed(revisions["new"])
        self.setInstalled(revisions["prod"])
        self.setPrevious(revisions["old"])

