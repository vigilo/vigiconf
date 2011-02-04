# -*- coding: utf-8 -*-
# vim: set et ts=4 sw=4:

from __future__ import absolute_import

from vigilo.vigiconf.lib.application import Application

from . import generator
from . import config

class Nagios(Application):

    name = "nagios"
    priority = 3
    validation = "validate.sh"
    start_command = "start.sh"
    stop_command = "stop.sh"
    generator = generator.NagiosGen
    group = "collect"
    defaults = config.DEFAULTS


