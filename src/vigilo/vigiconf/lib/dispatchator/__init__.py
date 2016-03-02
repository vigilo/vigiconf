################################################################################
#
# VigiConf
# Copyright (C) 2007-2016 CS-SI
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
"""
Classes concernant le L{Dispatchator<base.Dispatchator>}. Seule L{la factory
<factory.make_dispatchator>} est directement accessible au niveau du module.
"""

from __future__ import absolute_import

from vigilo.vigiconf.lib.dispatchator.factory import make_dispatchator

__all__ = ("make_dispatchator", )


# vim:set expandtab tabstop=4 shiftwidth=4:
