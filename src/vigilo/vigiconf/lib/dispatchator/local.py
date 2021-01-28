# -*- coding: utf-8 -*-
# Copyright (C) 2007-2021 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Ce module contient une sous-classe du L{Dispatchator<base.Dispatchator>}
limitée à C{localhost}.

L'implémentation sachant gérer les serveurs distants fait partie de
Vigilo Enterprise Edition.
"""

from __future__ import absolute_import

from vigilo.vigiconf.lib.dispatchator.base import Dispatchator
from vigilo.vigiconf.lib.exceptions import EditionError

from vigilo.common.gettext import translate
_ = translate(__name__)


class DispatchatorLocal(Dispatchator):
    """
    Implémentation du Dispatchator limitée à C{localhost}.
    """

    def server_status(self, servernames, status, no_deploy=False):
        raise EditionError(_("Vigilo server management is only available "
                             "in the Enterprise edition. Aborting."))



# vim:set expandtab tabstop=4 shiftwidth=4:
