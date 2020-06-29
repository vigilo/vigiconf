# -*- coding: utf-8 -*-
# Copyright (C) 2007-2020 CS GROUP – France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>


from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

from vigilo.vigiconf.lib.loaders import DBLoader
from vigilo.models.tables import Application


__docformat__ = "epytext"


class ApplicationLoader(DBLoader):
    """
    Charge les applications en base depuis le modèle mémoire.
    """

    def __init__(self, apps):
        self.apps = apps
        super(ApplicationLoader, self).__init__(Application, "name")

    def load_conf(self):
        LOGGER.info(_("Loading applications"))
        for app_obj in self.apps:
            app = dict(name=unicode(app_obj.name))
            self.add(app)
        LOGGER.info(_("Done loading applications"))
