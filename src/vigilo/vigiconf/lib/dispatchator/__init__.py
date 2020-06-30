# vim: fileencoding=utf-8 sw=4 ts=4 et ai
# Copyright (C) 2007-2020 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>
"""
Classes concernant le L{Dispatchator<base.Dispatchator>}. Seule L{la factory
<factory.make_dispatchator>} est directement accessible au niveau du module.
"""

from __future__ import absolute_import

from vigilo.vigiconf.lib.dispatchator.factory import make_dispatchator

__all__ = ("make_dispatchator", )


# vim:set expandtab tabstop=4 shiftwidth=4:
