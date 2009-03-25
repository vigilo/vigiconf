#!/usr/bin/env python
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
Wrapper for system commands
"""

import os
import subprocess

from lib import ConfMgrError


class SystemCommandError(ConfMgrError):
    """Exceptions involving L{SystemCommand} instances"""

    def __str__(self):
        return repr("SystemCommandError : "+self.value)


class SystemCommand(object):
    """
    Provide methods for executing shell commands
    @ivar mCommand: the command to execute
    @type mCommand: C{str}
    @ivar mResult: the result of the execution
    @type mResult: C{tuple}: (stdout, stderr)
    @ivar simulate: simulation mode (actually execute or not)
    @type simulate: C{boolean}
    """

    def __init__(self, iBaseCommand='', simulate=False):
        self.mCommand = iBaseCommand
        self.mResult = (None, None)
        self.simulate = simulate
        self.process = None
        
    def __str__(self):
        return "SystemCommand"
    
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

    def getResult(self):
        """
        @return: the concatenation of stdout and stderr from L{mResult}.
        @rtype: C{str}
        """
        message = ""
        for out in self.mResult:
            if out is not None:
                message += out
        return message
        
    def execute(self):
        """Executes the command"""
        if self.simulate:
            #print self.getCommand()
            return self.getCommand()
        newenv = os.environ.copy()
        newenv["LANG"] = "C"
        self.process = subprocess.Popen(self.getCommand(),
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        shell=True,
                                        env=newenv)
        self.mResult = self.process.communicate()
        if self.process.returncode != 0: # command failed
            raise SystemCommandError("command %s failed: %s" \
                    % (self.getCommand(), self.getResult()) )
    
    def integerReturnCode(self):
        """
        @return: the execution return code.
        @rtype: C{int}
        """
        return self.process.returncode
     
     

# vim:set expandtab tabstop=4 shiftwidth=4:
