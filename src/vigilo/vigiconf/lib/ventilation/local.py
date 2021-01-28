# -*- coding: utf-8 -*-
# Copyright (C) 2007-2021 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

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
