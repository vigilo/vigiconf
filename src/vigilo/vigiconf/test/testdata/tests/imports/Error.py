# -*- coding: utf-8 -*-
# Copyright (C) 2011-2020 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Le test de supervision défini par ce module est FICTIF.
Il est utilisé lors des tests unitaires pour valider le comportement
du chargeur de tests pour certains cas particuliers.
"""

from vigilo.vigiconf.lib.confclasses.test import Test
from vigilo.vigiconf.lib import VigiConfError

from vigilo.common.gettext import translate
_ = translate(__name__)


class Error(Test):
    def add_test(self):
        raise VigiConfError(_("Import test was successful"))
