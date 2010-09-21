# -*- coding: utf-8 -*-
# vim:set expandtab tabstop=4 shiftwidth=4:
################################################################################
#
# Copyright (C) 2007-2010 CS-SI
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
################################################################################

from __future__ import absolute_import

import os

import pkg_resources

from .exceptions import VigiConfError, EditionError, ParsingError

from vigilo.common.conf import settings
settings.load_module(__name__)

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)


__all__ = ("VigiConfError", "EditionError", "ParsingError",
           "setup_plugins_path")


def setup_plugins_path():
    """Très fortement inspiré de Trac"""
    plugins_path = os.path.realpath(os.path.join(
        settings["vigiconf"].get("pluginsdir", "/etc/vigilo/vigiconf/plugins")
    ))
    distributions, errors = pkg_resources.working_set.find_plugins(
        pkg_resources.Environment(plugins_path)
    )
    for dist in distributions:
        LOGGER.debug('Adding plugin %s from %s', dist, dist.location)
        pkg_resources.working_set.add(dist)

    def _log_error(item, e):
        if isinstance(e, pkg_resources.DistributionNotFound):
            LOGGER.debug('Skipping "%s": ("%s" not found)', item, e)
        elif isinstance(e, pkg_resources.VersionConflict):
            LOGGER.error(_('Skipping "%s": (version conflict "%s")'), item, e)
        elif isinstance(e, pkg_resources.UnknownExtra):
            LOGGER.error(_('Skipping "%s": (unknown extra "%s")'), item, e)
        elif isinstance(e, ImportError):
            LOGGER.error(_('Skipping "%s": (can\'t import "%s")'), item, e)
        else:
            LOGGER.error(_('Skipping "%s": (error "%s")'), item, e)

    for dist, e in errors.iteritems():
        _log_error(dist, e)

