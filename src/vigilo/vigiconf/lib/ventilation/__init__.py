# -*- coding: utf-8 -*-
################################################################################
#
# VigiConf
# Copyright (C) 2007-2013 CS-SI
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
Ventilation of the supervised assets on the Vigilo servers
"""

from __future__ import absolute_import

from pkg_resources import working_set

from vigilo.vigiconf import conf

__all__ = ("Ventilator", "get_ventilator")


class Ventilator(object):
    """Ventilation interface"""

    def __init__(self, apps):
        self.apps = apps

    def ventilate(self):
        raise NotImplementedError

    def ventilation_by_appname(self, ventilation): # pylint: disable-msg=R0201
        vba = {}
        for host in ventilation:
            vba[host] = {}
            for app, vserver in ventilation[host].iteritems():
                vba[host][app.name] = vserver
        return vba

    def servers_for_app(self, ventilation, app): # pylint: disable-msg=R0201
        servers = set()
        for host in ventilation:
            if app not in ventilation[host]:
                continue
            vsrvs = ventilation[host][app]
            if isinstance(vsrvs, basestring):
                vsrv = vsrvs
            else:
                vsrv = vsrvs[0]
            servers.add(vsrv)
        return servers


def get_ventilator(apps):
    """Ventilation factory"""
    if getattr(conf, "appsGroupsByServer", None):
        for entry in working_set.iter_entry_points(
                        "vigilo.vigiconf.extensions", "ventilator"):
            ventilator_class = entry.load()
            return ventilator_class(apps)
    # Community Edition, ventilator is not available.
    from .local import VentilatorLocal
    return VentilatorLocal(apps)

