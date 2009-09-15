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
This module contain the various dispatch modes. In the Community Edition,
only the local mode is available.
"""

from __future__ import absolute_import

import os
import sys
import glob

from ... import conf
from .. import ConfMgrError, EditionError

def getinstance():
    """
    Factory for the L{Dispatchator<dispatchator.Dispatchator>} children.

    @returns: L{local<lib.dispatchmodes.local.DispatchatorLocal>} or
        L{remote<lib.dispatchmodes.remote.DispatchatorRemote>} instance of the
        Dispatchator, depending on the Community or Enterprise Edition
    """
    if hasattr(conf, "appsGroupsByServer"):
        try:
            from .remote import DispatchatorRemote
        except ImportError:
            message = "You are trying remote deployment on the Community " \
                     +"edition. This feature is only available in the " \
                     +"Enterprise edition. Aborting."
            raise EditionError(message)
        _dispatchator = DispatchatorRemote()
    else:
        from .local import DispatchatorLocal
        _dispatchator = DispatchatorLocal()
    return _dispatchator


# vim:set expandtab tabstop=4 shiftwidth=4:
