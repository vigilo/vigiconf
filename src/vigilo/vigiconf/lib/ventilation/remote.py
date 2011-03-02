# -*- coding: utf-8 -*-
################################################################################
#
# VigiConf
# Copyright (C) 2007-2011 CS-SI
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

# pylint: disable-msg=E1101

"""
Module in charge of finding the good server to handle a given application
for a given host defined in the configuration.

This file is part of the Enterprise Edition
"""

from __future__ import absolute_import

import zlib

from vigilo.models.session import DBSession
from vigilo.models import tables
from vigilo.models.tables.secondary_tables import SUPITEM_GROUP_TABLE

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib.exceptions import ParsingError, VigiConfError
from vigilo.vigiconf.lib.ventilation import Ventilator


__docformat__ = "epytext"
__all__ = ("VentilatorRemote", "NoServerAvailable")


class NoServerAvailable(VigiConfError):
    """
    Exception remontée quand il n'y a pas de serveur Vigilo où ventiler un
    groupe d'hôtes
    """
    pass

class VentilatorRemote(Ventilator):

    def __init__(self, apps):
        super(VentilatorRemote, self).__init__(apps)
        self.apps_by_appgroup = self.get_app_by_appgroup()
        self._cache = {"host": {},
                       "active_vservers": [],
                       "apps": {},
                       "prev_ventilation": {}
                       }

    def make_cache(self):
        """On peuple les caches."""
        # 1- Le cache des hôtes.
        for host in DBSession.query(tables.Host.idhost, tables.Host.name).all():
            self._cache["host"][host.name] = host.idhost
            self._cache["host"][host.idhost] = host.name

        # 2- Le cache des serveurs de supervision actifs.
        for vserver in DBSession.query(
                tables.VigiloServer
            ).filter(tables.VigiloServer.disabled == False
            ).all():
            self._cache["active_vservers"].append(vserver.name)

        # 3- Le cache des applications.
        for app in DBSession.query(
                tables.Application.idapp,
                tables.Application.name
            ).all():
            self._cache["apps"][app.name] = app.idapp

        # 4- La ventilation précédente.
        for appgroup in self.apps_by_appgroup:
            apps = [ self._cache["apps"][unicode(app.name)]
                     for app in self.apps_by_appgroup[appgroup]
                     if unicode(app.name) in self._cache["apps"] ]
            for ventilation in DBSession.query(
                    tables.VigiloServer.name,
                    tables.Ventilation.idhost
                ).distinct(
                ).join(tables.Ventilation,
                ).filter(tables.Ventilation.idapp.in_(apps)
                ).filter(tables.VigiloServer.disabled == False
                ).all():
                key = (self._cache["host"][ventilation.idhost], appgroup)
                self._cache["prev_ventilation"].setdefault(key, [])
                self._cache["prev_ventilation"][key].append(ventilation.name)

    def get_previous_servers(self, host, appgroup):
        """
        Retourne le nom des précédents serveurs Vigilo
        sur lequel l'hôte a été ventilé pour une
        application précise.

        @param  host: Nom de l'hôte dont on veut connaître
            la ventilation précédente.
        @type   host: C{str}
        @param  appgroup: Nom de l'application dont la ventilation
            nous intéresse.
        @type   appgroup: C{str}
        @return: Nom des serveurs Vigilo sur lequels l'hôte L{host}
            a été ventilé pour l'application L{appgroup}.
        @rtype: C{list} of C{str}
        """
        return self._cache["prev_ventilation"].get( (host, appgroup), [] )

    def get_host_ventilation_group(self, hostname, hostdata=None):
        if hostdata is None:
            hostdata = {}
        if "serverGroup" in hostdata and hostdata["serverGroup"]:
            if hostdata["serverGroup"].count("/") == 1:
                hostdata["serverGroup"] = hostdata["serverGroup"].lstrip("/")
            return hostdata["serverGroup"]
        groups = set()
        idhost = self._cache["host"].get(unicode(hostname))
        if not idhost:
            raise KeyError("Trying to ventilate host %s, but it's not in the "
                           "database yet" % hostname)
        hostgroups = DBSession.query(tables.SupItemGroup
                ).join(
                    (SUPITEM_GROUP_TABLE, SUPITEM_GROUP_TABLE.c.idgroup
                                          == tables.SupItemGroup.idgroup),
                ).filter(SUPITEM_GROUP_TABLE.c.idsupitem == idhost).all()
        for group in hostgroups:
            groups.add(group.get_top_parent().name)

        if not groups:
            raise ParsingError(_('Could not determine how to '
                'ventilate host "%s". Affect some groups to '
                'this host or use the ventilation attribute.') %
                hostname)

        if len(groups) != 1:
            raise ParsingError(_('Found multiple candidates for '
                    'ventilation (%(candidates)r) on "%(host)s", '
                    'use the ventilation attribute to select one.') % {
                    'candidates': u', '.join([unicode(g) for g in groups]),
                    'host': hostname,
                })
        ventilation = groups.pop()
        if ventilation.count("/") == 1:
            ventilation = ventilation.lstrip("/")
        hostdata['serverGroup'] = ventilation
        return ventilation

    def get_app_by_appgroup(self):
        appgroups = {}
        for app in self.apps:
            appgroups.setdefault(app.group, []).append(app)
        return appgroups

    def filter_vservers(self, vserverlist):
        """
        Filtre une liste pour ne garder que les serveurs qui ne sont pas
        désactivés.
        @param vserverlist: list de noms de serveurs Vigilo
        @type  vserverlist: C{list} de C{str}
        """
        return [ v for v in vserverlist
                 if v in self._cache["active_vservers"] ]

    def ventilate(self, fromdb=False): # pylint: disable-msg=W0221
        """
        Try to find the best server where to monitor the hosts contained in the
        I{conf}.

        @return: a dict of the ventilation result. The dict content is:
          - B{Key}: name of a host
          - B{value}: a dict in the form:
            - B{Key}: the name of an application for which we have to deploy a
              configuration for this host
              (Nagios, CorrSup, Collector...)
            - B{Value}: a list of vigilo server hostnames where the
              configuration for this host and application should be deployed

        I{Example}:

          >>> ventilate()
          {
          ...
          "my_host_name":
            {
              'collector': ['collect_server_pool1.domain.name'],
              'nagios': ['collect_server_pool1.domain.name'],
              'perfdata': ['collect_server_pool1.domain.name'],
            }
          ...
          }

        """
        LOGGER.debug("Ventilation begin")
        self.make_cache()

        # deux façons de récupérer les hôtes
        if not fromdb:
            # cas classique
            iter_hosts = conf.hostsConf.iteritems
        else:
            # désactivation d'un serveur : on reventile depuis la base
            def iter_hosts():
                for host in DBSession.query(tables.Host.name).all():
                    yield host.name, {}

        # On collecte tous les groupes d'hôtes
        hostgroups = {}
        for host, v in iter_hosts():
            hostgroup = self.get_host_ventilation_group(host, v)
            if hostgroup not in hostgroups:
                hostgroups[hostgroup] = []
            hostgroups[hostgroup].append(host)

        # On calcule les pools de ventilation pour chaque groupe d'application,
        # en prenant en compte les serveurs désactivés et le backup
        errors = set()
        r = {}
        for hostgroup, hosts in hostgroups.iteritems():
            for host in hosts:
                app_to_vservers = {}
                for appgroup in conf.appsGroupsByServer:
                    # On essaye de récupérer les serveurs Vigilo
                    # sur lesquels on peut ventiler. Il peut y en
                    # avoir 2 (un nominal et un backup) ou un seul
                    # (un backup) si tous les nominaux sont tombés.
                    try:
                        servers = self._ventilate_appgroup(appgroup,
                                                           hostgroup, host)
                    except NoServerAvailable, e:
                        errors.add(e.value)
                        continue
                    except VigiConfError, e:
                        errors.add(e.value)
                        continue
                    if servers is None:
                        continue
                    for app in self.apps_by_appgroup[appgroup]:
                        app_to_vservers[app] = servers
                r[host] = app_to_vservers

        for error in errors:
            LOGGER.warning(_("No server available for the appgroup %(appgroup)s"
                             " and the hostgroup %(hostgroup)s, skipping it"),
                           {"appgroup": error[0], "hostgroup": error[1]})

        #from pprint import pprint; pprint(r)
        LOGGER.debug("Ventilation end")
        return r

    def _ventilate_appgroup(self, appGroup, hostGroup, host):
        if appGroup not in self.apps_by_appgroup or \
                not self.apps_by_appgroup[appGroup]:
            return None # pas d'appli dans ce groupe
        if hostGroup not in conf.appsGroupsByServer[appGroup]:
            LOGGER.warning(_("Trying to ventilate hostgroup %(hostgroup)s "
                             "for appgroup %(appgroup)s, but the mapping is "
                             "not in appsGroupsByServer."),
                           { "hostgroup": hostGroup, "appgroup": appGroup})
            # Peut-être une erreur de conf. On ignore.
            return None

        vservers = []
        checksum = zlib.adler32(host)

        # On regarde quels sont les serveurs nominaux disponibles.
        nominal = conf.appsGroupsByServer[appGroup][hostGroup]
        nominal = self.filter_vservers(nominal) # ne garde que les actifs
        previous_servers = set(self.get_previous_servers(host, appGroup))

        # Parmi tous les serveurs Vigilo nominaux disponibles,
        # on en choisit un.
        if nominal:
            intersect = previous_servers & set(nominal)
            if intersect:
                vservers.append(intersect.pop())
            else:
                vservers.append(nominal[checksum % len(nominal)])

        # On regarde les serveurs de backup utilisables.
        backup_mapping = getattr(conf, "appsGroupsBackup", {})
        if appGroup in backup_mapping and \
                hostGroup in backup_mapping[appGroup]:
            backup = backup_mapping[appGroup][hostGroup]
            backup = self.filter_vservers(backup)

            if backup:
                intersect = previous_servers & set(backup)
                if intersect:
                    vservers.append(intersect.pop())
                else:
                    vservers.append(backup[checksum % len(backup)])

        if not vservers:
            # Aucun serveur disponible, même dans le backup.
            # On abandonne.
            raise NoServerAvailable((appGroup, hostGroup))
        return vservers


# vim:set expandtab tabstop=4 shiftwidth=4:
