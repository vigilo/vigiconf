# -*- coding: utf-8 -*-
################################################################################
#
# VigiConf
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
Local ventilation
"""

from __future__ import absolute_import

from vigilo.vigiconf import conf
from . import Ventilator


class VentilatorLocal(Ventilator):

    def ventilate(self):
        """Map every app to localhost (Community Edition)"""
        mapping = {}
        for host in conf.hostsConf.keys():
            mapping[host] = {}
            for app in self.apps:
                mapping[host][app] = "localhost"
        return mapping


# vim:set expandtab tabstop=4 shiftwidth=4:
