# -*- coding: utf-8 -*-
# Copyright (C) 2011-2019 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from __future__ import print_function
import sys, os, inspect, itertools
from epydoc.markup import epytext
from vigilo.vigiconf.lib.confclasses.test import TestFactory
from logging import getLogger

LOGGER = getLogger(__name__)

def _get_target_file():
    """
    Retourne le nom du fichier dans lequel la documentation
    des tests de supervision supportés par Vigilo sera écrite.
    """
    return os.path.join(os.path.dirname(__file__), 'suptests.rst')


def _prepare_table():
    widths = []
    table = []
    return table


def _to_unicode(line):
    if isinstance(line, unicode):
        return line
    if isinstance(line, str):
        return line.decode('utf-8', 'replace')
    raise NotImplementedError()

# Credit for this function goes to Paul Clinch:
# http://code.activestate.com/recipes/285264-natural-string-sorting/#c6
def keynat(string):
    r'''A natural sort helper function for sort() and sorted()
    without using regular expressions or exceptions.

    >>> items = ('Z', 'a', '10th', '1st', '9')
    >>> sorted(items)
    ['10th', '1st', '9', 'Z', 'a']
    >>> sorted(items, key=keynat)
    ['1st', '9', '10th', 'a', 'Z']
    '''
    it = type(1)
    r = []
    for c in string:
        if c.isdigit():
            d = int(c)
            if r and type( r[-1] ) == it:
                r[-1] = r[-1] * 10 + d
            else:
                r.append(d)
        else:
            r.append(c.lower())
    return r

def write_autodoc():
    """
    Génère automatiquement une documentation des tests de supervision
    supportés par Vigilo au format reStructuredText et l'enregistre
    dans le fichier retourné par L{_get_target_file}.

    Cf. ticket #932.
    """

    widths = []
    handle = open(_get_target_file(), 'w')
    handle.write(".. table:: Liste des tests de supervision "
                 "           disponibles dans Vigilo\n\n")

    test_factory = TestFactory('/')
    tests = test_factory.get_tests()

    # PHASE 1 : récupération de la documentation des tests.
    # Ce dictionnaire contiendra la documentation de chaque test
    # et de ses paramètres.
    tests_doc = {}
    for testname, test in sorted((t.get_fullname(), t) for t in tests):
        print("INFO: traitement du test '%s'" % testname)
        tests_doc[testname] = {
            'doc': '',
            'optional_params': {},
            'required_params': {},
            'defaults': {},
        }

        # Recopie la documentation de la classe,
        # qui devient celle du test représenté.
        test_doc = test.__doc__ or ""
        if not test_doc:
            print("WARNING: aucune description pour le test '%(test)s'" % {
                    'test': testname,
                  }, file=sys.stderr)

        errors = []
        test_doc = epytext.parse_docstring(test_doc, errors)
        if errors:
            print("WARNING: impossible de lire la documentation "
                  "du test '%(test)s'" % {
                    'test': testname,
                  }, file=sys.stderr)

            tests_doc[testname]['doc'] = ""
        else:
            tests_doc[testname]['doc'] = \
                test_doc.to_plaintext(None).strip().replace('\n', ' ')

        # Détermine les noms des paramètres
        # obligatoires et optionnels du test
        # pour cette classe d'équipements.
        func = getattr(test.add_test, 'wrapped_func', test.add_test)
        specs = list(inspect.getargspec(func))
        specs[0] = specs[0][1:]
        required = (isinstance(specs[3], tuple) and len(specs[3]) or 0)
        required = len(specs[0]) - required
        optional = specs[0][required:]
        required = specs[0][:required]

        # Prépare la liste des paramètres obligatoires/optionnels
        params = dict()
        params.update(zip(required, ('required_params', ) * len(required)))
        params.update(zip(optional, ('optional_params', ) * len(optional)))

        # Liste des valeurs par défaut
        default_values = dict(zip(optional, specs[3] or ()))

        # Prépare un espace pour stocker la documentation
        # sur les paramètres de ce test.
        for param, category in params.items():
            tests_doc[testname][category][param] = dict(
                doc='',
                type=None,
                default=default_values.get(param)
            )

        errors = []
        doc = epytext.parse_docstring(test.add_test.__doc__ or '', errors)
        if errors:
            print("WARNING: impossible de lire la documentation des "
                  "paramètres du test '%(test)s'" % {
                    'test': testname,
                  }, file=sys.stderr)
            continue

        unknown = []
        for field in doc.split_fields()[1]:
            # Si un paramètre inconnu est documenté...
            argname = field.arg()
            if field.tag() in ('param', 'type') and argname not in params:
                unknown.append(str(argname))
                continue

            if field.tag() == 'param':
                tests_doc[testname][params[argname]][argname]['doc'] = \
                    field.body().to_plaintext(None).strip().replace('\n', ' ')

            elif field.tag() == 'type':
                tests_doc[testname][params[argname]][argname]['type'] = \
                    field.body().to_plaintext(None).strip()

        if unknown:
            print("WARNING: les paramètres suivants du test '%(test)s' "
                  "sont inconnus mais documentés : '%(params)s'" % {
                    'params': ', '.join(unknown),
                    'test': testname,
                  }, file=sys.stderr)

        undocumented = []
        for param, category in params.items():
            if tests_doc[testname][category][param]['doc']:
                continue
            undocumented.append(param)

        if undocumented:
            print("WARNING: les paramètres suivants du test '%(test)s' "
                  "ne sont pas documentés: %(params)s" % {
                    'params': ', '.join(undocumented),
                    'test': testname,
                  }, file=sys.stderr)

    # PHASE 2 : transformation de la documentation en tableau
    #           avec les données formatées en reStructuredText.
    cells = [[], [], []]
    tests = sorted(tests_doc.iterkeys(), key=keynat)
    for test in tests:
        # Nom du test (colonne 1).
        cells[0].append('**%s**' % test)

        # Description du test (colonne 2).
        cells[1].append(tests_doc[test]['doc'])

        # Description des paramètres obligatoires du test (colonne 2).
        params = sorted(tests_doc[test]['required_params'].iterkeys(), key=keynat)
        if params:
            cells[1].append("")
            cells[1].append("Paramètres obligatoires du test :")

        for param in params:
            cells[1].append("")

            if tests_doc[test]['required_params'][param]['type']:
                type_info = "*%s* " % tests_doc[test]['required_params'][param]['type']
            else:
                type_info = ''

            param_doc = "* %s**%s**: %s" % (
                    type_info,
                    param,
                    tests_doc[test]['required_params'][param]['doc'],
                )
            cells[1].append(param_doc)

        # Description des paramètres optionnels du test (colonne 2).
        params = sorted(tests_doc[test]['optional_params'].iterkeys(), key=keynat)
        if params:
            cells[1].append("")
            cells[1].append("Paramètres optionnels du test :")

        for param in params:
            cells[1].append("")

            if tests_doc[test]['optional_params'][param]['type']:
                type_info = "*%s* " % tests_doc[test]['optional_params'][param]['type']
            else:
                type_info = ''

            param_doc = tests_doc[test]['optional_params'][param]['doc'].rstrip('.')
            param_def = tests_doc[test]['optional_params'][param]['default']

            if isinstance(type_info, unicode):
                type_info = type_info.encode('utf-8')
            if isinstance(param_doc, unicode):
                param_doc = param_doc.encode('utf-8')
            if isinstance(param_def, unicode):
                param_def = param_def.encode('utf-8')

            param_doc = "* %s**%s**: %s. Valeur par défaut: %s" % (
                    type_info,
                    param,
                    param_doc,
                    param_def,
                )
            cells[1].append(param_doc)

        padding = max(len(cells[0]), len(cells[1]))
        for i in xrange(3):
            if len(cells[i]) != padding:
                cells[i].extend([""] * (padding - len(cells[i])))

        # Marque la fin de la documentation de ce test.
        cells[0].append(None)
        cells[1].append(None)

    # PHASE 3 : représentation du tableau dans le fichier final.
    widths = []
    header = (
        "Nom du test",
        "Description",
    )

    for i in xrange(2):
        # Détermine la largeur à utiliser pour chacune des colonnes.
        # Il s'agit du max des largeurs des différentes entrées
        # de la colonne, y compris l'en-tête, plus deux (+2).
        # Le +2 permet d'ajouter un espace avant et après le texte,
        # ce qui évite des problèmes de délimitation du contenu des cases.
        widths.append(
            max(
                len(max(cells[i], key=lambda x: x is not None and len(x) or 0)),
                len(header[i])
            ) + 2
        )
    new_line = "+%s+" % "+".join(["-" * width for width in widths])
    header_line = new_line.replace('-', '=')

    data = [
        # En-tête.
        new_line,
        header,
        header_line,
    ]

    # Convertit les cellules du tableau en lignes de données.
    for i in xrange(len(cells[0])):
        # Si les cellules d'une ligne ne contiennent que des None,
        # on insère le délimiteur d'entrées à la place
        # (cf. formatage des tableaux en reStructuredText).
        if cells[0][i] is None and cells[1][i] is None:
            data.append(new_line)
            continue
        data.append( (cells[0][i], cells[1][i] ) )

    # Écrit le contenu du tableau ligne par ligne.
    for line in data:
        if isinstance(line, basestring):
            real_line = _to_unicode(line)
        else:
            # Il s'agit d'un itérable avec le contenu de chacune des cellules
            # de la ligne. On effectue le bourrage nécessaire pour aligner
            # les cellules
            real_line = [u""]
            for index, part in enumerate(line):
                real_line.append(u" " + _to_unicode(part).ljust(widths[index] - 1))
            real_line.append(u"")
            real_line = u"|".join(real_line)
        handle.write(" " * 4 + real_line.encode('utf-8') + "\n")

    handle.write("\n.. vim: set tw=79 :\n")
    handle.close()
    return 0


if __name__ == "__main__":
    sys.exit(write_autodoc())
