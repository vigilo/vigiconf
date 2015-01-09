# -*- coding: utf-8 -*-
################################################################################
#
# ConfigMgr Data Consistancy dispatchator
# Copyright (C) 2007-2015 CS-SI
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
Wrapper for system commands
"""

from __future__ import absolute_import

import os
import subprocess

from . import VigiConfError

from vigilo.common.gettext import translate
_ = translate(__name__)


class SystemCommand(object):
    """
    Provide methods for executing commands
    @ivar mCommand: the command to execute
    @type mCommand: C{list} or C{str}
    @ivar mResult: the result of the execution
    @type mResult: C{tuple}: (stdout, stderr)
    @ivar simulate: simulation mode (actually execute or not)
    @type simulate: C{boolean}
    """

    def __init__(self, iBaseCommand=None, simulate=False):
        if iBaseCommand is None:
            iBaseCommand = []
        self.mCommand = iBaseCommand
        self.mResult = (None, None)
        self.simulate = simulate
        self.process = None

    def __str__(self):
        return "<SystemCommand: %s>" % " ".join(self.mCommand)

    def setCommand(self, iCommand):
        """
        Sets L{mCommand}.
        @param iCommand: the command to execute
        @type  iCommand: C{str}
        """
        self.mCommand = iCommand

    def getCommand(self):
        """@return: L{mCommand}"""
        return self.mCommand

    def getResult(self, stdout=True, stderr=True):
        """
        @return: the concatenation of stdout and stderr from L{mResult}.
        @rtype: C{str}
        """
        message = ""
        if stdout and self.mResult[0]:
            message += self.mResult[0]
        if stderr and self.mResult[1]:
            message += self.mResult[1]
        return message

    def execute(self):
        """Executes the command"""
        if self.simulate:
            #print self.getCommand()
            return self.getCommand()
        newenv = os.environ.copy()
        newenv["LANG"] = "C"
        newenv["LC_ALL"] = "C"
        try:
            self.process = subprocess.Popen(self.getCommand(),
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE,
                                            env=newenv)
        except OSError:
            raise MissingCommand(self.getCommand())
        self.mResult = self.process.communicate()
        if self.process.returncode != 0: # command failed
            raise SystemCommandError(self.getCommand(), self.process.returncode,
                                     self.getResult())
        return self.mResult

    def integerReturnCode(self):
        """
        @return: the execution return code.
        @rtype: C{int}
        """
        return self.process.returncode


class SystemCommandError(VigiConfError):
    """Exceptions involving C{SystemCommand} instances"""

    def __init__(self, command, returncode, message):
        super(SystemCommandError, self).__init__(message)
        self.command = command
        self.returncode = returncode
        self.message = self.value

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        cmd = self.command
        if isinstance(cmd, list):
            cmd = " ".join(cmd)
        return _("Command \"%(cmd)s\" failed with code %(code)s "
                 "and message: %(msg)s") % {
                   'cmd': cmd,
                   'code': self.returncode,
                   'msg': self.message.decode("utf8", "replace"),
                 }
        # TODO: L'encodage UTF-8 est hardcodé ci-dessus, détecter celui du
        # système

    def __repr__(self):
        return "<%s: code %d and message %s>" \
               % (type(self).__name__, self.returncode, self.message)


class MissingCommand(SystemCommandError):
    def __init__(self, command):
        if isinstance(command, basestring):
            command = command.split()
        super(MissingCommand, self).__init__(command, 255,
            _("Missing command: %s") % command[0])

    def __unicode__(self):
        return self.message

# vim:set expandtab tabstop=4 shiftwidth=4:
