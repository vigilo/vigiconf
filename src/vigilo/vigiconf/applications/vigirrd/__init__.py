# -*- coding: utf-8 -*-
# vim: set et ts=4 sw=4:
#pylint: disable-msg=C0111
# Copyright (C) 2011-2014 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from __future__ import absolute_import

from vigilo.vigiconf.lib.application import Application

from . import generator
from . import config


class VigiRRD(Application):

    name = "vigirrd"
    priority = -1
    validation = "validate.sh"
    start_command = "sudo '%%(httpd_init)s' reload"
    stop_command = None
    generator = generator.VigiRRDGen
    group = "metrology"
    defaults = config.DEFAULTS

