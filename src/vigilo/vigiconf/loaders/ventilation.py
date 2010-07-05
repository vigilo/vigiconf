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

from vigilo.models.tables import Host, Application, Ventilation, VigiloServer

from vigilo.vigiconf.lib.dbloader import DBLoader


__docformat__ = "epytext"


class VentilationLoader(DBLoader):
    """
    Charge la ventilation en base depuis le modèle mémoire.

    Dépend de ApplicationLoader et de VigiloServerLoader.
    """

    
    def __init__(self, ventilation):
        """
        @param ventilation: dict generated by findAServerForEachHost
        @type ventilation: C{dict}
        
        Example:
          >>> findAServerForEachHost()
          {
          ...
          "my_host_name":
            {
              'apacheRP': 'presentation_server.domain.name',
              'collector': 'collect_server_pool1.domain.name',
              'corrsup': 'correlation_server.domain.name',
              'corrtrap': 'correlation_server.domain.name',
              'dns': 'infra_server.domain.name',
              'nagios': 'collect_server_pool1.domain.name',
              'nagvis': 'presentation_server.domain.name',
              'perfdata': 'collect_server_pool1.domain.name',
              'rrdgraph': 'store_server_pool2.domain.name',
              'storeme': 'store_server_pool2.domain.name',
              'supnav': 'presentation_server.domain.name'
            }
          ...
          }
        """
        super(VentilationLoader, self).__init__(Ventilation)
        self.ventilation = ventilation

    def load(self):
        self.load_conf()
        # Pas de cleanup, on est une table de liaison donc c'est géré par les
        # clés étrangères
        DBSession.flush()

    def load_conf(self):
        DBSession.query(Ventilation).delete()
        DBSession.flush()
        for hostname, serverbyapp in self.ventilation.iteritems():
            host = Host.by_host_name(unicode(hostname))
            
            for appname, server in serverbyapp.iteritems():
                vigiloserver = VigiloServer.by_vigiloserver_name(unicode(server))
                application =  Application.by_app_name(unicode(appname))
                v = Ventilation(idhost=host.idhost,
                                idvigiloserver=vigiloserver.idvigiloserver,
                                idapp=application.idapp)
                DBSession.merge(v)

