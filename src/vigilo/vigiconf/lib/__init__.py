# -*- coding: utf-8 -*-
# vim:set expandtab tabstop=4 shiftwidth=4:
# Copyright (C) 2007-2019 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from __future__ import absolute_import

import os

from .exceptions import VigiConfError, EditionError, ParsingError

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)


__all__ = ("VigiConfError", "EditionError", "ParsingError",
           "SNMP_ENTERPRISE_OID")

SNMP_ENTERPRISE_OID = "14132"
