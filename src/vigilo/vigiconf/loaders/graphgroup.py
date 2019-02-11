# -*- coding: utf-8 -*-
# Copyright (C) 2007-2019 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

from vigilo.models.session import DBSession
from vigilo.models.tables import GraphGroup

from vigilo.vigiconf.lib.loaders import DBLoader

from vigilo.vigiconf import conf

__docformat__ = "epytext"


class GraphGroupLoader(DBLoader):
    """
    Charge les groupes de graphes en base depuis le modèle mémoire.
    """

    def __init__(self):
        super(GraphGroupLoader, self).__init__(GraphGroup, "name")

    def load_conf(self):
        LOGGER.info(_("Loading graph groups"))
        groupnames = set()
        for hostname in conf.hostsConf:
            for groupname in conf.hostsConf[hostname]['graphGroups']:
                groupnames.add(unicode(groupname))
        for groupname in groupnames: # déduplication
            self.add({"name": groupname})
        LOGGER.info(_("Done loading graph groups"))

    def update(self, data):
        instance = super(GraphGroupLoader, self).update(data)
        DBSession.flush()
        return instance
