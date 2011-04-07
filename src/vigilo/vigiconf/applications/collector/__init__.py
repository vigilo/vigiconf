# -*- coding: utf-8 -*-
# vim: set et ts=4 sw=4:
#pylint: disable-msg=C0111

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

