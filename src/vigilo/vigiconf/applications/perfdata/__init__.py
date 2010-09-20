# -*- coding: utf-8 -*-
# vim: set et ts=4 sw=4:

from __future__ import absolute_import

from vigilo.vigiconf.lib.application import Application

from . import generator

class PerfData(Application):

    name = "perfdata"
    priority = -1
    validation = "validate.sh"
    start_command = None
    stop_command = None
    generator = generator.PerfDataGen
    group = "collect"


