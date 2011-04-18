# -*- coding: utf-8 -*-
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
Ce module contient la I{Factory} du L{Dispatchator<base.Dispatchator>}.
Dans Vigilo Community Edition, seule l'implémentation L{DispatchatorLocal
<local.DispatchatorLocal>} est disponible.
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
    @return: La meilleure sous-classe de L{Dispatchator<base.Dispatchator>}
    disponible, en fonction de l'édition de Vigilo.
    """
    if hasattr(conf, "appsGroupsByServer"):
        for entry in working_set.iter_entry_points(
                        "vigilo.vigiconf.extensions", "dispatchator_remote"):
            return entry.load()
        message = _("You are attempting a remote deployment on the Community "
                    "edition. This feature is only available in the "
                    "Enterprise edition. Aborting.")
        raise EditionError(message)
    else:
        from .local import DispatchatorLocal
        return DispatchatorLocal


def make_dispatchator():
    """
    I{Factory} du L{Dispatchator<base.Dispatchator>}. Retourne l'implémentation
    correspondante à l'édition de Vigilo utilisée.
    """
    d_class = get_dispatchator_class()
    # servers
    srv_mgr = get_server_manager()
    srv_mgr.list()
    # apps
    app_mgr = ApplicationManager()
    app_mgr.list()
    # revision
    rev_mgr = RevisionManager()
    # generators
    gen_mgr = GeneratorManager(app_mgr.applications)
    # instanciation
    d = d_class(app_mgr, rev_mgr, srv_mgr, gen_mgr)
    return d


# vim:set expandtab tabstop=4 shiftwidth=4:
