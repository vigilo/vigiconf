# -*- coding: utf-8 -*-
# Copyright (C) 2007-2020 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>
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
mode = "onedir"
confid = ""

#hostsConf = hostfactory.hosts
hostsConf = {}


def loadConf():
    load_general_conf(['general'])
    load_xml_conf()

def load_general_conf(subdirs=None):
    # General configuration
    conf = {
        'apps': set(),
        'apps_conf': {},
        'hostsGroups': {},
        'hostsConf': {},
        'dependencies': {},
        'dynamicGroups': {},
        'mode': 'onedir',
        'confid': '',
        'appsGroupsByServer': {},
        'appsGroupsBackup': {},
    }
    conf_keys = conf.keys()

    if subdirs is None:
        subdirs = []

    for confsubdir in subdirs:
        try:
            files = glob.glob(os.path.join(settings["vigiconf"].get("confdir"),
                                           confsubdir, "*.py"))
            files.sort()
            for fileF in files:
                execfile(fileF, conf)
        except Exception as e:
            sys.stderr.write("Error while parsing %s: %s\n"%(fileF, str(e)))
            raise e

    for appsgroups in ('appsGroupsByServer', 'appsGroupsBackup'):
        for function in conf.get(appsgroups, {}):
            for group in list(conf[appsgroups][function].keys()):
                conf[appsgroups][function][group] = \
                    [v.lower() for v in conf[appsgroups][function][group]]

    # On répercute la configuration dans l'environnement global.
    for conf_key in conf_keys:
        globals()[conf_key] = conf[conf_key]

def load_xml_conf(validation=True):
    """
    Load the confdir directory, looking for configuration files.
    @returns: None, but sets global variables as described above.
    """
    global hostsConf
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
    except ParsingError as e:
        LOGGER.error(_("Error loading configuration"))
        raise e


# vim:set expandtab tabstop=4 shiftwidth=4:
