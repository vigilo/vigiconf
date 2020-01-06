# -*- coding: utf-8 -*-
# Copyright (C) 2011-2020 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

name = 'vigiconf'
project = u'VigiConf'

pdf_documents = [
    ('admin', "admin-%s" % name, u"%s : Manuel administrateur" % project, u'Vigilo'),
    ('dev', "dev-%s" % name, u"%s : Manuel développeur" % project, u'Vigilo'),
]

latex_documents = [
    ('admin', 'admin-%s.tex' % name, u"%s : Manuel administrateur" % project,
     'AA100004-2/UTI00003', 'vigilo'),
    ('dev', 'dev-%s.tex' % name, u"%s : Manuel développeur" % project,
     'AA100004-2/DEV00001', 'vigilo'),
]

execfile("../buildenv/doc/conf.py")
