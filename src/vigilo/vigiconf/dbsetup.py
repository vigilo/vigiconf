# -*- coding: utf-8 -*-
# Copyright (C) 2006-2016 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""Initialisation de la base de données."""

from vigilo.common.conf import settings
settings.load_module(__name__)
from vigilo.models.session import DBSession
from vigilo.models import tables
from vigilo.vigiconf.lib.dispatchator.revisionmanager import RevisionManager

def populate_db(bind):
    """
    Initialisation de la base de données pour VigiConf.
    """
    scm_version = tables.Version.by_object_name(RevisionManager.version_key)
    if scm_version is None:
        scm_version = tables.Version(
            name=RevisionManager.version_key,
            version=0
        )
        DBSession.add(scm_version)
        DBSession.flush()
