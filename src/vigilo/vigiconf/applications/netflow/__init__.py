# -*- coding: utf-8 -*-
# vim: set et ts=4 sw=4:
from . import generator
#pylint: disable-msg=C0111

from __future__ import absolute_import

from vigilo.vigiconf.lib.application import Application



class Netflow(Application):

    name = "netflow"
    priority = 3
    validation = "validate.sh"
    start_command = "sudo /etc/init.d/nfacctd start"
    stop_command = "sudo /etc/init.d/nfacctd stop"
    generator = generator.NetflowGen
    group = "collect"


