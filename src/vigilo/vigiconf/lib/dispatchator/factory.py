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

from pkg_resources import working_set

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib import EditionError
from vigilo.vigiconf.lib.server import get_server_manager
from vigilo.vigiconf.lib.generators import GeneratorManager
from vigilo.vigiconf.lib.application import ApplicationManager
from .revisionmanager import RevisionManager

from vigilo.common.gettext import translate
_ = translate(__name__)


def get_dispatchator_class():
    """
    Factory for the L{Dispatchator<vigilo.vigiconf.lib.dispatchator.Dispatchator>}
    children.

    @return: the proper class of the Dispatchator, depending on the Community
        or Enterprise Edition
    """
    if hasattr(conf, "appsGroupsByServer"):
        for entry in working_set.iter_entry_points(
                        "vigilo.vigiconf.extensions", "dispatchator_remote"):
            return entry.load()
        message = _("You are trying remote deployment on the Community "
                    "edition. This feature is only available in the "
                    "Enterprise edition. Aborting.")
        raise EditionError(message)
    else:
        from .local import DispatchatorLocal
        return DispatchatorLocal


def make_dispatchator():
    """Factory pour le Dispatchator"""
    d_class = get_dispatchator_class()
    # apps
    apps_mgr = ApplicationManager()
    apps_mgr.list()
    # revision
    rev_mgr = RevisionManager()
    # servers
    srv_mgr = get_server_manager()
    srv_mgr.list()
    # generators
    gen_mgr = GeneratorManager(apps_mgr.applications)
    # instanciation
    d = d_class(apps_mgr, rev_mgr, srv_mgr, gen_mgr)
    d.link_apps_to_servers()
    return d


# vim:set expandtab tabstop=4 shiftwidth=4:
