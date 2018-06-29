# -*- coding: utf-8 -*-
# Copyright (C) 2018 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from __future__ import absolute_import, print_function

import sys, os, inspect
import json
import logging
from epydoc.markup import epytext

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

def format(testfactory, hclasses, available_hclasses):
    """
    Formatte la liste des tests et classes de tests disponibles
    dans une structure JSON.
    """

    res = {}
    for test in testfactory.get_tests(hclasses):
        testname = test.get_fullname()
        test_doc = test.__doc__ or ""

        errors = []
        test_doc = epytext.parse_docstring(test_doc, errors)
        if errors:
            LOGGER.error(_("Could not parse documentation about '%s'") % testname)
            continue

        data = {
            'description': test_doc.to_plaintext(None)
                            .strip().replace('\n', ' ')
        }

        # Détermine les noms des arguments obligatoires et optionnels du test.
        specs = list(inspect.getargspec(test.add_test))
        # On supprime "self" de la liste des arguments obligatoires.
        specs[0] = specs[0][1:]
        required = len(specs[0]) - (isinstance(specs[3], tuple) and len(specs[3]) or 0)
        optional = specs[0][required:]
        required = specs[0][:required]

        # Liste des valeurs par défaut
        default_values = dict(zip(optional, specs[3] or ()))

        doc = epytext.parse_docstring(test.add_test.__doc__ or '', errors)
        if errors:
            LOGGER.error(_("Could not parse arguments for '%s'") % testname)
            continue

        args = {}
        for argname in required:
            args[argname] = {}
        for argname in optional:
            args[argname] = { 'default': default_values[argname] }

        for field in doc.split_fields()[1]:
            # On ignore les types de tags non supportés.
            if field.tag() not in ('param', 'type'):
                continue

            if argname not in required and argname not in optional:
                LOGGER.error(_("Unknown argument '%(arg)s' for '%(test)s'") % {
                    'arg': argname,
                    'test': testname,
                })
                continue

            argname = field.arg()
            field_value = field.body().to_plaintext(None).strip()

            if field.tag() == 'param':
                key = 'description'
            else:
                key = 'type'
                if field_value in ('str', 'unicode', 'threshold'):
                    field_value = 'string'

            args[argname][key] = field_value

        if args:
            data['args'] = args
        res[testname] = data

    return res


def dump(testfactory, hclasses, available_hclasses):
    """
    Affiche la liste des tests et classes de tests disponibles
    sous forme JSON sur la sortie standard.
    """

    indent = LOGGER.isEnabledFor(logging.DEBUG) and 2 or None
    print(json.dumps(
        format(testfactory, hclasses, available_hclasses),
        indent=indent))
