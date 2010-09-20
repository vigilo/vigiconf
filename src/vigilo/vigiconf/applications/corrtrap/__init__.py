# -*- coding: utf-8 -*-
# vim: set et ts=4 sw=4:

from __future__ import absolute_import

from vigilo.vigiconf.lib.application import Application

from . import generator

class CorrTrap(Application):

    name = "corrtrap"
    priority = 3
    validation = "validate.sh"
    start_command = "sudo /etc/init.d/vigilo-corrtrap start"
    stop_command = "sudo /etc/init.d/vigilo-corrtrap stop"
    generator = generator.CorrTrapGen
    group = "trap"


