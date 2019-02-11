# -*- coding: utf-8 -*-
# Copyright (C) 2018-2019 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from __future__ import absolute_import, print_function

import sys, os, inspect
import json
import logging
from epydoc.markup import epytext

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

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

        # Si le wrapper n'est pas présent, cela signifie que le test
        # ne prend aucun argument.
        if not hasattr(test.add_test, 'wrapped_func'):
            func = test.add_test
        else:
            func = test.add_test.wrapped_func

        # Détermine les noms des arguments obligatoires et optionnels du test.
        specs = list(inspect.getargspec(func))
        # On supprime "self" de la liste des arguments obligatoires.
        specs[0] = specs[0][1:]
        required = len(specs[3]) if isinstance(specs[3], tuple) else 0
        required = len(specs[0]) - required
        optional = specs[0][required:]
        required = specs[0][:required]

        # Liste des valeurs par défaut
        default_values = dict(zip(optional, specs[3] or ()))

        args = OrderedDict()
        testargs = getattr(test.add_test, 'args', ())
        if set(testargs) != set(optional + required):
            LOGGER.error(_("Not all of the arguments have been described in '%s'") % testname)
            continue

        for argname in reversed(testargs):
            validator, display_name, description = testargs[argname]

            description = epytext.parse_docstring(description, errors)
            if errors:
                LOGGER.error(_("Could not parse documentation about argument "
                               "'%(arg)s' for test '%(test)s'") % {
                                    'arg': argname,
                                    'test': testname,
                               })
                continue


            args[argname] = {
                'description': description.to_plaintext(None).strip(),
                'display_name': display_name,
                'validation': validator.export(),
            }

            if argname in optional:
                args[argname]['default'] = default_values[argname]

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

