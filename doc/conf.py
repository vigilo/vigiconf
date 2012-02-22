# -*- coding: utf-8 -*-

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
