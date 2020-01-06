# -*- coding: utf-8 -*-
# Copyright (C) 2007-2020 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>
"""
Classes concernant les L{serveurs<base.Server>} Vigilo. Seule L{la factory
<factory.get_server_manager>} du L{ServerManager<manager.ServerManager>} est
directement accessible au niveau du module.
"""

from __future__ import absolute_import

from vigilo.vigiconf.lib.server.factory import get_server_manager

__all__ = ("get_server_manager", )


# vim:set expandtab tabstop=4 shiftwidth=4:
