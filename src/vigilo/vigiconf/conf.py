################################################################################
#
# ConfigMgr configuration loader
# Copyright (C) 2007-2009 CS-SI
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
# pylint: disable-msg=C0103
"""
Configuration loader based on python files in the "general" subdirectory,
providing the global configuration, and a number of other subdirectories
containing XML files, providing the main configuration.
"""

from __future__ import absolute_import

import glob
import sys
import os

from vigilo.common.conf import settings
settings.load_module(__name__)

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

from .lib import ParsingError
from .lib.confclasses.host import HostFactory
from .lib.confclasses.hosttemplate import HostTemplateFactory
from .lib.confclasses.test import TestFactory


__docformat__ = "epytext"


def loadConf():
    load_general_conf()
    load_xml_conf()

def load_general_conf():
    # General configuration
    for confsubdir in [ "general", ]:
        try:
            files = glob.glob(os.path.join(settings["vigiconf"].get("confdir"),
                                           confsubdir, "*.py"))
            files.sort(key=lambda f: os.path.splitext(f)[0])
            #print files
            for fileF in files:
                execfile(fileF, globals())
                #print "Sucessfully parsed %s"%fileF
        except Exception, e:
            sys.stderr.write("Error while parsing %s: %s\n"%(fileF, str(e)))
            raise e

def load_xml_conf(validation=True):
    """
    Load the confdir directory, looking for configuration files.
    @returns: None, but sets global variables as described above.
    """
    LOGGER.info(_("Loading XML configuration"))
    # Initialize global objects and only use those
    testfactory = TestFactory(confdir=settings["vigiconf"].get("confdir"))
    hosttemplatefactory = HostTemplateFactory(testfactory)
    hostfactory = HostFactory(
                    os.path.join(settings["vigiconf"].get("confdir"), "hosts"),
                    hosttemplatefactory,
                    testfactory,
                  )
    hostsConf = hostfactory.hosts
    # Parse hosts
    try:
        hostfactory.load(validation=validation)
    except ParsingError, e:
        LOGGER.error(_("Error loading configuration"))
        raise e



# Initialize global paths
CODEDIR = os.path.dirname(__file__)

# Initialize global conf variables
apps = set()
apps_conf = {}

# TODO: en base, plus de python
hostsGroups = {}

hostsConf = {}
dependencies = {}
dynamicGroups = {}
dns = {}
mode = "onedir"
confid = ""

#hostsConf = hostfactory.hosts
hostsConf = {}


# vim:set expandtab tabstop=4 shiftwidth=4:
