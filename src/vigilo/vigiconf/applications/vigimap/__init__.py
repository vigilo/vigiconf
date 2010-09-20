# -*- coding: utf-8 -*-
# vim: set et ts=4 sw=4:

from __future__ import absolute_import

from vigilo.vigiconf.lib.application import Application

from . import generator

class VigiMap(Application):

    name = "vigimap"
    priority = -1
    validation = None
    start_command = None
    stop_command = None
    generator = generator.VigiMapGen
    group = "interface"

