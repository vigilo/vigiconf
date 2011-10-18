# -*- coding: utf-8 -*-

project = u'VigiConf'

pdf_documents = [
        ('util', "utilisateur-vigiconf", "VigiConf : Manuel utilisateur", u'Vigilo'),
]

latex_documents = [
        ('util', 'utilisateur-vigiconf.tex', u"VigiConf : Manuel utilisateur",
         'AA100004-2/UTI00003', 'vigilo'),
]

execfile("../buildenv/doc/conf.py")
