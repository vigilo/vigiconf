# -*- coding: utf-8 -*-
# Copyright (C) 2011-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

name = u'vigiconf'
project = u'VigiConf'

pdf_documents = [
        ('util', "utilisateur-%s" % name, "%s : Manuel utilisateur" % project, u'Vigilo'),
]

latex_documents = [
        ('util', 'utilisateur-%s.tex' % name, u"%s : Manuel utilisateur" % project,
         'AA100004-2/UTI00003', 'vigilo'),
]

execfile("../buildenv/doc/conf.py")
execfile("autodoc.py")
