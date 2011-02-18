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

from vigilo.vigiconf.lib.loaders import DBLoader

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)


__docformat__ = "epytext"


class VentilationLoader(DBLoader):
    """
    Charge la ventilation en base depuis le modèle mémoire.

    Dépend de ApplicationLoader et de VigiloServerLoader.
    """

    def __init__(self, ventilation, applications):
        """
        @param ventilation: dictionnaire généré par le
            L{ventilator<vigilo.vigiconf.lib.ventilator.Ventilator>}
        @type  ventilation: C{dict}
        @param applications: les applications gérées par le
            L{dispatchator<vigilo.vigiconf.lib.dispatchator>}
        @type  applications: C{list}

        Exemple::
          >>> ventilator.ventilate()
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
        self.applications = applications

    def load(self):
        self.load_conf()
        # Pas de cleanup, on est une table de liaison donc c'est géré par les
        # clés étrangères
        DBSession.flush()

    def load_conf(self):
        current = {}
        apps_location = {}
        for v in DBSession.query(Ventilation).all():
            current[(v.idhost, v.idvigiloserver, v.idapp)] = v
            apps_location.setdefault(v.idapp, set()).add(v.idvigiloserver)
        LOGGER.debug("Current ventilation entries: %d" % len(current))

        vigiloservers = {}
        for vigiloserver in DBSession.query(VigiloServer).all():
            vigiloservers[vigiloserver.name] = vigiloserver
            vigiloservers[vigiloserver.idvigiloserver] = vigiloserver

        applications = {}
        for application in DBSession.query(Application).all():
            applications[application.name] = application
            applications[application.idapp] = application

        new_apps_location = {}
        for hostname, serversbyapp in self.ventilation.iteritems():
            idhost = DBSession.query(Host.idhost).filter(
                Host.name == unicode(hostname)).scalar()

            for app_obj, servernames in serversbyapp.iteritems():
                if isinstance(servernames, basestring):
                    servernames = [servernames, ]
                # on ne met en base que le serveur nominal
                servername = servernames[0]
                vigiloserver = vigiloservers[unicode(servername)]
                application =  applications[unicode(app_obj.name)]
                key = (idhost, vigiloserver.idvigiloserver,
                       application.idapp)
                if key in current:
                    del current[key]
                else:
                    v = Ventilation(idhost=idhost,
                                idvigiloserver=vigiloserver.idvigiloserver,
                                idapp=application.idapp)
                    DBSession.add(v)
                new_apps_location.setdefault(application.idapp, set()
                                        ).add(vigiloserver.idvigiloserver)
        #DBSession.flush()
        # et maintenant on supprime ce qui reste
        LOGGER.debug("Obsolete ventilation entries: %d" % len(current))
        for v in current.values():
            DBSession.delete(v)
        # Vérifions qu'on a pas complètement supprimé une application d'un serveur
        for idapp, app_servers in apps_location.iteritems():
            new_app_servers = new_apps_location.get(idapp, set())
            orphan_servers = app_servers - new_app_servers
            if not orphan_servers:
                continue
            dbapp = applications[idapp]
            if dbapp.name not in [ a.name for a in self.applications ]:
                LOGGER.warning(_("The application %s has been removed from "
                                 "the configuration, it needs to be stopped "
                                 "manually"), dbapp.name)
                continue
            for app in self.applications:
                if app.name == dbapp.name:
                    break
            for idvserver in orphan_servers:
                vserver = vigiloservers[idvserver]
                app.servers[vserver.name] = ["stop", ]

