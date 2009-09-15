################################################################################
#
# ConfigMgr CorrSecu configuration file generator
# Copyright (C) 2007 CS-SI
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
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

"""Generator for the security correlator (CorrSecu)"""

from __future__ import absolute_import

from .. import conf
from . import Templator 

class CorrSecuTpl(Templator):
    """Generator for the security correlator (CorrSecu)"""

    def generate(self):
        """Generate files"""
        for hostdata in self.mapping.values():
            if 'corrsecu' in hostdata:
                dirName = "%s/%s/corrsecu" \
                          % (self.baseDir, hostdata['corrsecu'])
                for i in ['reglesSecu.conf']:
                    self.copyFile("%s/corrsecu/%s"%(os.path.join(conf.CONFDIR, "filetemplates"), i),
                                  "%s/%s"%(dirName, i))



# vim:set expandtab tabstop=4 shiftwidth=4:
