# -*- coding: utf-8 -*-
"""Insère des données de test dans la base de données."""

import atexit
from vigilo.common.conf import settings
settings.load_module('vigilo.models')

from vigilo.models.configure import configure_db
configure_db(settings['database'], 'sqlalchemy_',
	settings['database']['db_basename'])

from vigilo.models.session import DBSession
from vigilo.models.tables import VigiloServer

def commit_on_exit():
    """
    Effectue un COMMIT sur la transaction à la fin de l'exécution
    du script d'insertion des données de test.
    """
    import transaction
    transaction.commit()

atexit.register(commit_on_exit)

def create_vigiloserver(name):
    v = VigiloServer(name=name)
    DBSession.add(v)
    DBSession.flush()
    return v

create_vigiloserver(u'supserver.example.com')