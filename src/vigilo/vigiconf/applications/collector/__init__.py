# -*- coding: utf-8 -*-
# vim: set et ts=4 sw=4:
#pylint: disable-msg=C0111
# Copyright (C) 2011-2020 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from __future__ import absolute_import

from vigilo.vigiconf.lib.application import Application

from . import generator


class Collector(Application):

    name = "collector"
    priority = -1
    validation = "validate.sh"
    start_command = None
    stop_command = None
    generator = generator.CollectorGen
    group = "collect"

