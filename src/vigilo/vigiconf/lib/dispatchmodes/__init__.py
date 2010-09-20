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
This module contain the various dispatch modes. In the Community Edition,
only the local mode is available.
"""

from __future__ import absolute_import

import os
import sys
import glob

from pkg_resources import working_set

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib import EditionError

from vigilo.common.gettext import translate
_ = translate(__name__)

def getinstance():
    """
    Factory for the L{Dispatchator<vigilo.vigiconf.lib.dispatchator.Dispatchator>}
    children.

    @returns: L{local<vigilo.vigiconf.lib.dispatchmodes.local.DispatchatorLocal>}
        or L{remote<vigilo.vigiconf.lib.dispatchmodes.remote.DispatchatorRemote>}
        instance of the Dispatchator, depending on the Community or Enterprise
        Edition
    """
    if hasattr(conf, "appsGroupsByServer"):
        for entry in working_set.iter_entry_points(
                        "vigilo.vigiconf.extensions", "dispatchator_remote"):
            dr_class = entry.load()
            return dr_class()
        message = _("You are trying remote deployment on the Community "
                    "edition. This feature is only available in the "
                    "Enterprise edition. Aborting.")
        raise EditionError(message)
    else:
        from .local import DispatchatorLocal
        return DispatchatorLocal()


# vim:set expandtab tabstop=4 shiftwidth=4:
