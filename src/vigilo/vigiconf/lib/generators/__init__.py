# -*- coding: utf-8 -*-
# Copyright (C) 2007-2020 CS GROUP – France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>
"""
Generators for the Vigilo Config Manager
"""

from __future__ import absolute_import

from .base import Generator
from .file import FileGenerator
from .manager import GeneratorManager, GenerationError

