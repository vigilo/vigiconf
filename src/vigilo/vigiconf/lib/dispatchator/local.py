################################################################################
#
# VigiConf
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
This module contains the localhost-only implementation of the Dispatchator.
The multi-server implementation is part of the Enterprise Edition.
"""

from __future__ import absolute_import

from vigilo.vigiconf.lib.dispatchator.base import Dispatchator
from vigilo.vigiconf.lib.exceptions import EditionError

from vigilo.common.gettext import translate
_ = translate(__name__)


class DispatchatorLocal(Dispatchator):
    """A localhost-only implementation of the Dispatchator."""

    def getServersForApp(self, app):
        """
        Get the list of server names for this app. In this
        implementation, return only localhost.
        @param app: the application to consider
        @type  app: L{lib.application.Application}
        @rtype: C{list} of C{str}
        """
        return [ "localhost" ]

    def server_status(self, servernames, status, no_deploy=False):
        raise EditionError(_("Vigilo server management is only available "
                             "in the Enterprise edition. Aborting."))



# vim:set expandtab tabstop=4 shiftwidth=4:
