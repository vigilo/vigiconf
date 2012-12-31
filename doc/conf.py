# -*- coding: utf-8 -*-
# Copyright (C) 2011-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

name = 'vigiconf'
project = u'VigiConf'

pdf_documents = [
    ('util', "util-%s" % name, u"%s : Manuel utilisateur" % project, u'Vigilo'),
    ('dev', "dev-%s" % name, u"%s : Manuel développeur" % project, u'Vigilo'),
]

latex_documents = [
    ('util', 'util-%s.tex' % name, u"%s : Manuel utilisateur" % project,
     'AA100004-2/UTI00003', 'vigilo'),
    ('dev', 'dev-%s.tex' % name, u"%s : Manuel développeur" % project,
     'AA100004-2/DEV00001', 'vigilo'),
]

execfile("../buildenv/doc/conf.py")
