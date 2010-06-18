#!/usr/bin/env python
# -*- coding: utf-8 -*-
################################################################################
#
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

import os

from vigilo.common.conf import settings
from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.models.session import DBSession

from vigilo.models.tables import VigiloServer

from vigilo.vigiconf.lib.dbloader import DBLoader

from vigilo.vigiconf import conf

__docformat__ = "epytext"


class VigiloServerLoader(DBLoader):
    """
    Charge les applications en base depuis le modèle mémoire.

    Exemple:
        appsGroupsByServer = {
            'collect' : {
                'P-F'             : ['srv1.vigilo'],
                'Servers'         : ['srv2.vigilo'],
                'Telecom'         : ['srv3.vigilo', 'srv4.vigilo'],
            },
            'metrology' : {
                'P-F'             : ['srv1.vigilo'],
                'Servers'         : ['srv2.vigilo'],
                'Telecom'         : ['srv5.vigilo'],
            },
        }
    """
    
    def __init__(self):
        super(VigiloServerLoader, self).__init__(VigiloServer, "name")

    def load_conf(self):
        servers = set()
        if hasattr(conf, "appsGroupsByServer"):
            configured_servers = conf.appsGroupsByServer.values()
        else:
            configured_servers = [{"hostgroup": ["localhost"]},]
        for appgroup in configured_servers:
            for vservers in appgroup.values():
                for vserver in vservers:
                    servers.add(vserver)
        for servername in servers:
            self.add({"name": servername})


