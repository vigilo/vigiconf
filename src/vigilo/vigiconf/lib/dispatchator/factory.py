# -*- coding: utf-8 -*-
# Copyright (C) 2007-2020 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

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
    if getattr(conf, "appsGroupsByServer", None):
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


def make_dispatchator(user=None, message=None):
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
    rev_mgr = RevisionManager(user, message)
    # generators
    gen_mgr = GeneratorManager(app_mgr.applications)
    # instanciation
    d = d_class(app_mgr, rev_mgr, srv_mgr, gen_mgr)
    return d


# vim:set expandtab tabstop=4 shiftwidth=4:
