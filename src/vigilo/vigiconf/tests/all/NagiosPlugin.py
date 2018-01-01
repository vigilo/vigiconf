# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903
# Copyright (C) 2006-2018 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

import urllib
from vigilo.vigiconf.lib.confclasses.test import Test


class NagiosPlugin(Test):
    """Test générique pour utiliser un plugin Nagios indépendant"""

    def add_test(self, name, command, metrics=None, unit=''):
        """
        @param name: Le nom du service dans Nagios (service_description)
        @param command: Le nom de la commande à utiliser (check_command)
        """
        # Service
        self.add_external_sup_service(name, command)

        # Métrologie
        if metrics:
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
