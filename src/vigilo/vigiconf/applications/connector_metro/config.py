# -*- coding: utf-8 -*-
# Copyright (C) 2011-2013 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

DEFAULTS = {
    "step": 300,
    "heartbeat": 600,
    "rra": {
        "basic": [
            # step=300 secondes => 5 minutes
            # période=5minutes, 600 valeurs => 3000minutes=50heures (~ 2 jours)
            { "type": "AVERAGE", "xff": 0.5, "step": 1, "rows": 600 },
            # période=6*5 minutes (30minutes), 700 valeurs => 21000minutes=350heures (~ 14.5 jours)
            { "type": "AVERAGE", "xff": 0.5, "step": 6, "rows": 700 },
            # période=24*5 minutes (2heures), 775 valeurs => 1550heures=64jours (~ 2 mois)
            { "type": "AVERAGE", "xff": 0.5, "step": 24, "rows": 775 },
            # période=288*5 minutes (24heures), 775 valeurs => 775jours (~ 2 ans)
            { "type": "AVERAGE", "xff": 0.5, "step": 288, "rows": 732},
        ],
        "netflow": [
            # step=300 secondes => 5 minutes
            # période=5minutes, 4320 valeurs => 21600minutes=360heures (15 jours)
            { "type": "AVERAGE", "xff": 0.5, "step": 1, "rows": 4320 },
            # période=12*5minutes (1heure), 744 valeurs => 744heures=31jours (~1 mois)
            { "type": "AVERAGE", "xff": 0.5, "step": 12, "rows": 744 },
            # période=288*5minutes(1jour), 366 valeurs => 366jours (1 an)
            { "type": "AVERAGE", "xff": 0.5, "step": 288, "rows": 366},
        ],
        # Cette définition de RRAs est utile
        # pour les jauges à valeurs discrètes,
        # ex: nombre d'utilisateurs/sessions TCP,
        # nombre d'appels en cours, etc.
        "discrete": [
            { "type": "LAST", "xff": 0.5, "step": 1, "rows": 600 },
            { "type": "AVERAGE", "xff": 0.5, "step": 6, "rows": 700 },
            { "type": "AVERAGE", "xff": 0.5, "step": 24, "rows": 775 },
            { "type": "AVERAGE", "xff": 0.5, "step": 288, "rows": 732},
        ],
    },
}
