# -*- coding: utf-8 -*-
# vim: set et ts=4 sw=4:
#pylint: disable-msg=C0111

from __future__ import absolute_import

from vigilo.vigiconf.lib.application import Application

from . import generator


class ConnectorNagios(Application):

    name = "connector-nagios"
    priority = -1
    validation = "validate.sh"
    start_command = "sudo /etc/init.d/vigilo-connector-nagios reload"
    stop_command = None
    generator = generator.ConnectorNagiosGen
    group = "collect"


