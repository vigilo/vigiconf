# -*- coding: utf-8 -*-
################################################################################
#
# VigiConf
# Copyright (C) 2007-2014 CS-SI
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
Classes concernant les L{serveurs<base.Server>} Vigilo. Seule L{la factory
<factory.get_server_manager>} du L{ServerManager<manager.ServerManager>} est
directement accessible au niveau du module.
"""

from __future__ import absolute_import

from vigilo.vigiconf.lib.server.factory import get_server_manager

__all__ = ("get_server_manager", )


# vim:set expandtab tabstop=4 shiftwidth=4:
