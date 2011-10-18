# -*- coding: utf-8 -*-

project = u'VigiConf'

pdf_documents = [
        ('util', "vigiconf-util", "VigiConf : Manuel utilisateur", u'Vigilo'),
]

latex_documents = [
  #('%(master_str)s', '%(project_fn)s.tex', u'%(project_doc_texescaped_str)s',
  ('util', 'util.tex', u'VigiConf : Manuel utilisateur', 'AA100004-2/UTI00003', 'vigilo'),
]

execfile("../buildenv/doc/conf.py")
