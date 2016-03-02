# -*- coding: utf-8 -*-
################################################################################
#
# VigiConf server factory
# Copyright (C) 2007-2016 CS-SI
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
Ce module contient les I{Factories} des sous-classes de L{Server<base.Server>}
et L{ServerManager<manager.ServerManager>}.

Dans Vigilo Community Edition, seules les sous-classes L{ServerLocal} et
L{ServerManagerLocal} sont disponibles.
"""

from __future__ import absolute_import

import socket
try:
    import netifaces
except ImportError:
    netifaces = None
from pkg_resources import working_set

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib import EditionError
from vigilo.vigiconf.lib.server.local import ServerLocal, ServerManagerLocal


class ServerFactory(object):
    """
    I{Factory} pour L{Server<base.Server>}: retourne une instance de la bonne
    sous-classe.

    @cvar localnames: Ensemble des noms/adresses faisant référence
        à la machine locale.
    @type localnames: C{set}
    """

    localnames = set()

    def __init__(self):
        self.remote_class = self.find_remote_class()

        if not self.localnames:
            # L'union permet ici de modifier le set de la classe "en place",
            # ce qui a le même effet qu'un cache.
            self.localnames |= self._find_local_names()

    def _find_local_names(self):
        """
        Retourne l'ensemble des noms et des adresses
        faisant référence à la machine locale.

        @return: Ensemble des noms et adresses de la machine locale.
        @rtype: C{set}
        """
        localnames = set([socket.gethostname(), 'localhost'])
        addresses = set(['127.0.0.1', '::1'])

        # Permet de garder un fonctionnement minimum lorsque le paquet
        # netifaces n'est pas disponible (cas de certaines anciennes
        # distributions Linux).
        if netifaces:
            # Récupération de la liste des addresses (IPv4/IPv6)
            # des différentes interfaces réseau de la machine locale.
            for iface in netifaces.interfaces():
                families = netifaces.ifaddresses(iface)
                for family in families:
                    # On ne garde que les addresses IPv4/IPv6.
                    if family not in (netifaces.AF_INET, netifaces.AF_INET6):
                        continue
                    for entry in families[family]:
                        if 'addr' in entry:
                            addresses.add(entry['addr'])

        # Les adresses IPs de la machine sont reconnues
        # comme "aliases" de la machine.
        localnames |= addresses

        # Résolution inverse des adresses IP
        # pour obtenir le reste des aliases.
        for address in addresses:
            try:
                aliases = socket.gethostbyaddr(address)

                # Nom principal correspondant à l'adresse.
                localnames.add(aliases[0])

                # Autres aliases pour cette adresse.
                localnames |= set(aliases[1])
            except socket.error:
                continue

        return localnames

    def find_remote_class(self): # pylint: disable-msg=R0201
        for entry in working_set.iter_entry_points(
                        "vigilo.vigiconf.extensions", "server_remote"):
            sr_class = entry.load()
            return sr_class
        return None

    def makeServer(self, name):
        """
        Returns the right server object, depending on the hostname
        @param name: the hostname of the Server object to create
        @type  name: C{str}
        @returns: Server object with the provided hostname
        @rtype: L{Server}
        """
        if name in self.localnames:
            return ServerLocal(name)
        else:
            if self.remote_class is None:
                raise EditionError(_("On the Community Edition, you can "
                                     "only use localhost"))
            return self.remote_class(name)


def get_server_manager_class():
    """
    Retourne la bonne sous-classe de L{ServerManager<manager.ServerManager>}
    en fonction de l'édition de Vigilo.
    """
    if getattr(conf, "appsGroupsByServer", None):
        for entry in working_set.iter_entry_points(
                        "vigilo.vigiconf.extensions", "server_manager_remote"):
            return entry.load()
        message = _("Remote server management is not possible with the "
                    "Community edition. This feature is only available "
                    "in the Enterprise edition. Aborting.")
        raise EditionError(message)
    else:
        return ServerManagerLocal

def get_server_manager():
    """
    I{Factory} pour L{ServerManager<manager.ServerManager>}: retourne une
    instance de la meilleure sous-classe en fonction de l'édition de Vigilo.
    """
    server_factory = ServerFactory()
    sm_class = get_server_manager_class()
    return sm_class(server_factory)


# vim:set expandtab tabstop=4 shiftwidth=4:
