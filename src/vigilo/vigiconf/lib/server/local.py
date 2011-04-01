# -*- coding: utf-8 -*-
################################################################################
#
# Copyright (C) 2007-2011 CS-SI
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
Ce module contient les implémentations des classes L{Server<base.Server>} et
L{ServerManager<manager.ServerManager>} limitées à C{localhost}.

Elles concernent Vigilo Community Edition.
"""

from __future__ import absolute_import

import os

from vigilo.common.gettext import translate
_ = translate(__name__)

from .base import Server, ServerError
from .manager import ServerManager
from vigilo.vigiconf.lib.systemcommand import SystemCommandError


class ServerManagerLocal(ServerManager):

    def list(self):
        """
        Get all server names from configuration
        @return: the servers names from the configuration. In our case, a list
            with only the localhost is returned
        @rtype: C{list} of C{str}
        """
        self.servers = {"localhost": ServerLocal("localhost")}

    def restrict(self, servernames):
        return

class ServerLocal(Server):
    """Implémentation de L{Server} pour C{localhost}"""

    def __init__(self, iName):
        # Superclass constructor
        Server.__init__(self, iName)

    def deployTar(self):
        tar = os.path.join(self.getBaseDir(), "%s.tar" % self.getName())
        cmd = self.createCommand(["vigiconf-local", "receive-conf", tar])
        try:
            cmd.execute()
        except SystemCommandError, e:
            raise ServerError(_("Can't deploy the tar archive for server "
                                "%(server)s: %(error)s") % {
                                    'server': self.getName(),
                                    'error': e.value,
                                })

    def is_enabled(self): # pylint: disable-msg=R0201
        return True

# vim:set expandtab tabstop=4 shiftwidth=4:
