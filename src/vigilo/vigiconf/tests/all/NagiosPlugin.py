# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903
# Copyright (C) 2006-2019 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from __future__ import unicode_literals

import urllib

from vigilo.vigiconf.lib.confclasses.validators import arg, String, List
from vigilo.vigiconf.lib.confclasses.test import Test
from vigilo.common.gettext import l_


class NagiosPlugin(Test):
    """Test générique pour utiliser un plugin Nagios externe"""

    @arg(
        'name', String,
        l_('Display name'),
        l_("""
            Name to display in the GUI.

            This setting also controls the name of the service
            created in Nagios (service_description).
        """)
    )
    @arg(
        'command', String,
        l_('Command'),
        l_("Command to execute to call the plugin (check_command)")
    )
    @arg(
        'metrics', List(types=String),
        l_('Metrics'),
        l_("List of metrics returned by the plugin that should be graphed")
    )
    @arg(
        'unit', String,
        l_('Unit'),
        l_("Unit used by the plugin's metrics")
    )
    def add_test(self, name, command, metrics=(), unit=''):
        # Service
        self.add_external_sup_service(name, command)

        # Métrologie
        if not metrics:
            return

        rrd_metrics = []
        for metric in metrics:
            # On construit un nom unique pour le fichier RRD
            # qui stockera les données de performance,
            # sur le modèle "NagiosPlugin-<service URL-encodé>@<métrique>"
            # et le nom du service pour rendre le nom du fichier unique.
            rrd = "NagiosPlugin-%s@%s" % (urllib.quote_plus(name), metric)
            self.add_perfdata_handler(name, rrd, metric, metric,
                                      rra_template='discrete')
            rrd_metrics.append(rrd)

        # Un graphe est automatiquement créé avec toutes les métriques.
        self.add_graph("Plugin-%s" % name, rrd_metrics, 'lines', unit)


# vim:set expandtab tabstop=4 shiftwidth=4:
