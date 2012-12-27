# -*- coding: utf-8 -*-
################################################################################
#
# Copyright (C) 2007-2012 CS-SI
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

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

from vigilo.models.tables import VigiloServer
from vigilo.vigiconf.lib.loaders import DBLoader
from vigilo.vigiconf import conf

__docformat__ = "epytext"


class VigiloServerLoader(DBLoader):
    """
    Charge les serveurs de supervision depuis le fichier de configuration
    `appgroups-servers.py`.

    Exemple:
    >>> appsGroupsByServer = {
    ...     'collect' : {
    ...         'Vigilo'          : ['srv1.vigilo'],
    ...         'Servers'         : ['srv2.vigilo'],
    ...         'Telecom'         : ['srv3.vigilo', 'srv4.vigilo'],
    ...     },
    ...     'metrology' : {
    ...         'Vigilo'          : ['srv1.vigilo'],
    ...         'Servers'         : ['srv2.vigilo'],
    ...         'Telecom'         : ['srv5.vigilo'],
    ...     },
    ... }
    """

    def __init__(self):
        super(VigiloServerLoader, self).__init__(VigiloServer, "name")

    def load_conf(self):
        LOGGER.info(_("Loading Vigilo servers"))
        servers = set()
        if getattr(conf, "appsGroupsByServer", None):
            configured_servers = conf.appsGroupsByServer.values()
        else:
            configured_servers = [{"hostgroup": ["localhost"]}, ]
        if getattr(conf, "appsGroupsBackup", None):
            configured_servers.extend(conf.appsGroupsBackup.values())
        for appgroup in configured_servers:
            for vservers in appgroup.values():
                for vserver in vservers:
                    servers.add(vserver)
        for servername in servers:
            self.add({"name": unicode(servername)})
        LOGGER.info(_("Done loading Vigilo servers"))
