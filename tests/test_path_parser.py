# -*- coding: utf-8 -*-
"""Teste l'analyseur de chemins."""
import unittest
from vigilo.vigiconf.lib.confclasses import parse_path

class TestPathParser(unittest.TestCase):
    def test_accept_valid_paths(self):
        """L'analyseur doit interpréter correctement les chemins valides."""
        paths = {
            'A':            ['A'],
            '/A/B/C':       ['A', 'B', 'C'],
            '/A/B/C/':      ['A', 'B', 'C'],    # On ignore le "/" final.
            r'/A\\B':       [r'A\B'],
            r'/A\/B':       [r'A/B'],
            r'/A\\\/B/C':   [r'A\/B', 'C'],
        }
        for path, parts in paths.iteritems():
            self.assertEqual(parts, parse_path(path))

    def test_escapes_sequences_handling(self):
        """L'analyseur doit refuser des séquences inconnues."""
        paths = [
            r'/A\AB',
            r'/A\nB',   # On doit ignorer les séquences d'échappement Python.
            r'/A\rB',
            r'/A\tB',
        ]
        for path in paths:
            self.assertEqual(None, parse_path(path))

    def test_reject_invalid_paths(self):
        """L'analyseur doit rejeter les chemins invalides."""
        paths = [
            '',         # Chemin vide.
            '/',        # Chemin vide.
            'A/B',      # Chemin relatif contenant plusieurs composantes.
            '/A//B',    # Composante de chemin vide.
        ]
        for path in paths:
            self.assertEqual(None, parse_path(path))

