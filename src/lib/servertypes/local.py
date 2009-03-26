################################################################################
#
# Copyright (C) 2007-2009 CS-SI
#
# This program is free software; you can redistribute it and/or modify
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
The local host Server instance
"""

import conf
from lib.server import Server
from lib.systemcommand import SystemCommand

class ServerLocal(Server):
    """The local host"""

    def __init__(self, iName):
        # Superclass constructor
        Server.__init__(self, iName)

    def createCommand(self, iCommand):
        """
        @param iCommand: command to execute
        @type  iCommand: C{str}
        @return: the command instance
        @rtype: L{SystemCommand<lib.systemcommand.SystemCommand>}
        """
        c = SystemCommand(iCommand)
        c.simulate = getattr(conf, "simulate", False)
        return c

    def _builddepcmd(self):
        """
        Build the deployment command line
        """
        _commandline = "sudo rm -rf %s/new && " \
                        % conf.baseConfDir \
                      +"sudo cp -pr %s/%s %s/new && " \
                        % (self.getBaseDir(), self.getName(),
                           conf.baseConfDir) \
                      +"sudo chmod -R o-w %s/new" \
                        % conf.baseConfDir
        return _commandline


# vim:set expandtab tabstop=4 shiftwidth=4:
