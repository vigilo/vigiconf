# -*- coding: utf-8 -*-
# vim: set et ts=4 sw=4:

from __future__ import absolute_import

from vigilo.vigiconf.lib.application import Application

from . import generator

class SnmpTT(Application):

    name = "snmptt"
    priority = 3
    validation = "validate.sh"
    start_command = "sudo /etc/init.d/snmptt start"
    stop_command = "sudo /etc/init.d/snmptt stop"
    generator = generator.SnmpTTGen
    group = "collect"


