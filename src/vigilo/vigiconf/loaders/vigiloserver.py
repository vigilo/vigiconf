# -*- coding: utf-8 -*-
# Copyright (C) 2007-2021 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

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
