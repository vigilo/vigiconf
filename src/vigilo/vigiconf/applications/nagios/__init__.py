# -*- coding: utf-8 -*-
# vim: set et ts=4 sw=4:

from __future__ import absolute_import

from vigilo.vigiconf.lib.application import Application

from . import generator

class Nagios(Application):

    name = "nagios"
    priority = 3
    validation = "validate.sh"
    start_command = "sudo /etc/init.d/nagios start"
    stop_command = "sudo /etc/init.d/nagios stop ; (while i in `seq 30` ; do pgrep nagios >/dev/null || break; sleep 1;done)"
    generator = generator.NagiosGen
    group = "collect"

