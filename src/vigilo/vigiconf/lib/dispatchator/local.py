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
