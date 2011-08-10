# -*- coding: utf-8 -*-
################################################################################
#
# VigiConf
# Copyright (C) 2007-2011 CS-SI
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
################################################################################

from vigilo.common.conf import settings
settings.load_module(__name__)
# On modifie le préfixe, afin de pouvoir travailler
# sur des données temporaires.
settings['database']['db_basename'] += 'tmp_'

from vigilo.models.configure import configure_db
configure_db(settings['database'], 'sqlalchemy_')

from vigilo.models.session import metadata, DBSession
from vigilo.models import configure

# L'import permet de pré-charger les tables dans l'objet metadata,
# en plus de rendre accessible les objets de l'ORM.
from vigilo.models import tables

from sqlalchemy.schema import DDL
from sqlalchemy.sql import expression
from sqlalchemy.types import Integer
import transaction

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

__all__ = (
    'prepare_tmp_tables',
    'finalize_tmp_tables',
)

def _get_table_columns(table):
    """
    Retourne une liste avec les noms des colonnes de la table,
    une fois les règles d'échappement appliquées.

    @param table: Table pour laquelle on veut connaître
        les noms (échappés) des colonnes.
    @type table: C{sqlalchemy.schema.Table}
    @return: Liste des noms échappés des colonnes de la table.
    @rtype: C{list} of C{str}
    """
    return [table.compile().preparer.format_column(c) for c in table.c]

def prepare_tmp_tables():
    LOGGER.info(_("Creating temporary tables with a copy of current data"))

    views = [
        tables.GroupPath.__tablename__,
        tables.UserSupItem.__tablename__,
    ]
    base_len = len(configure.DB_BASENAME)

    # Tout d'abord, on supprime les tables temporaires
    # (résidus d'un précédent deploy par exemple).
    mapped_tables = metadata.tables.copy()
    del mapped_tables[tables.GroupPath.__tablename__]
    del mapped_tables[tables.UserSupItem.__tablename__]

    # On force les nouvelles tables à être temporaires.
    # Elles ne sont visibles que par la session courante
    # et sont supprimées automatiquement à la fin de la session.
    for table in metadata.sorted_tables:
        table._prefixes.insert(0, 'TEMPORARY')

    # Puis on les recrée.
    metadata.create_all(tables=mapped_tables.itervalues())
    metadata.create_all(tables=[
        tables.GroupPath.__table__,
        tables.UserSupItem.__table__
    ])

    # On copie les données des tables finales vers les tables temporaires,
    # sauf pour les vues (dans lesquelles on ne peut pas insérer de données).
    for table in metadata.sorted_tables:
        if table.name in views:
            continue

        orig_name = table.name[:base_len - 4] + table.name[base_len:]
        columns = _get_table_columns(table)
        DDL(
            "INSERT INTO %(fullname)s(%(columns)s) "
            "SELECT %(columns)s FROM %(original)s;",
            context={
                'original': orig_name,
                'columns': ",".join(columns),
            },
        ).execute(metadata.bind, table)

        # On initialise les séquences dans copies aux valeurs courantes
        # des séquences dans les tables finales.
        for column in table.c:
            # Une séquence est créée par SQLAlchemy pour chaque colonne
            # de type entier auto-incrémentale qui appartient à
            # la clé primaire et n'est pas une référence externe.
            if isinstance(column.type, Integer) and column.primary_key \
                and column.autoincrement and not column.foreign_keys:
                copy_name = '%s_%s_seq' % (table.name, column.name)
                orig_name = copy_name[:base_len - 4] + copy_name[base_len:]

                DDL(
                    """
                    SELECT setval('%(copy)s', last_value)
                    FROM %(original)s;
                    """,
                    context={
                        'original': orig_name,
                        'copy': copy_name,
                    },
                ).execute(metadata.bind, table)

        # Recommandé sur les forums pour mettre à jour la stratégie
        # du plannificateur de requêtes de PostgreSQL. Pas standard.
        DDL("ANALYZE %(fullname)s;").execute(metadata.bind, table)
    LOGGER.info(_("Done copying data"))
    transaction.commit()

def finalize_tmp_tables():
    views = [
        tables.GroupPath.__tablename__,
        tables.UserSupItem.__tablename__,
    ]
    base_len = len(configure.DB_BASENAME)

    raw_dbms_version = DBSession.execute(
        'SELECT character_value '
        'FROM information_schema.sql_implementation_info '
        'WHERE implementation_info_name = :info;',
        params={
            'info': "DBMS VERSION",
            'table': tables.SupItem.__tablename__,
        }
    ).fetchone().character_value
    dbms_version = map(int, raw_dbms_version.split('.'))

    # Si on tourne sous PostgreSQL 8.4+, on peut utiliser TRUNCATE pour vider
    # les tables; les triggers de Slony seront correctement déclenchés.
    if dbms_version[0] > 8 or \
        (dbms_version[0] == 8 and dbms_version[1] >= 4):
        purge_cmd = "TRUNCATE TABLE ONLY %(original)s CASCADE;"
        strategy = "TRUNCATE"

    # Sinon, on est forcés d'utiliser un DELETE (beaucoup plus lent).
    else:
        purge_cmd = "DELETE FROM %(original)s;"
        strategy = "DELETE"

    LOGGER.info(_("Copying temporary tables to their final destination using "
                "%(strategy)s strategy for PostgreSQL %(major)d.%(minor)d.%(patch)d"), {
                    'strategy': strategy,
                    'major': dbms_version[0],
                    'minor': dbms_version[1],
                    'patch': dbms_version[2],
                })

    transaction.begin()
    connection = DBSession.connection()
    DDL("SET CONSTRAINTS ALL DEFERRED;").execute(connection, None)

    # Ajout de verrous pour limiter les risques d'accès concurrents.
    for table in metadata.sorted_tables:
        if table.name in views:
            continue
        orig_name = table.name[:base_len - 4] + table.name[base_len:]
        DDL(
            "LOCK TABLE %(original)s IN SHARE ROW EXCLUSIVE MODE;",
            context={'original': orig_name}
        ).execute(connection, table)

    # On purge le contenu des tables finales.
    for table in metadata.sorted_tables:
        if table.name in views:
            continue

        # On vide la table d'origine à l'aide de la commande appropriée.
        orig_name = table.name[:base_len - 4] + table.name[base_len:]
        DDL(
            purge_cmd,
            context={'original': orig_name}
        ).execute(connection, table)

    # On copie les données des tables temporaires vers les tables finales,
    # après avoir vidé ces dernières. On ne peut pas le faire juste après
    # les DELETE à cause des CASCADEs SQL.
    for table in metadata.sorted_tables:
        if table.name in views:
            continue

        orig_name = table.name[:base_len - 4] + table.name[base_len:]
        columns = _get_table_columns(table)
        DDL(
            "INSERT INTO %(original)s(%(columns)s) "
            "SELECT %(columns)s FROM %(fullname)s;",
            context={
                'original': orig_name,
                'columns': ",".join(columns),
            },
        ).execute(connection, table)

        # On réinitalise les séquences originales avec le résultat
        # des traitements sur les tables temporaires.
        for column in table.c:
            # Une séquence est créée par SQLAlchemy pour chaque colonne
            # de type entier auto-incrémentale qui appartient à
            # la clé primaire et n'est pas une référence externe.
            if isinstance(column.type, Integer) and column.primary_key \
                and column.autoincrement and not column.foreign_keys:
                copy_name = '%s_%s_seq' % (table.name, column.name)
                orig_name = copy_name[:base_len - 4] + copy_name[base_len:]

                DDL(
                    """
                    SELECT setval('%(original)s', last_value)
                    FROM %(copy)s;
                    """,
                    context={
                        'original': orig_name,
                        'copy': copy_name,
                    },
                ).execute(connection, table)

        # Recommandé sur les forums pour mettre à jour la stratégie
        # du plannificateur de requêtes de PostgreSQL. Pas standard.
        DDL("ANALYZE %(fullname)s;").execute(connection, table)

    # Sans ce COMMIT manuel, les modifications sont perdues
    # avant qu'on arrive à l'étape de validation du chargement,
    # et ce même si on appelle transaction.commit() ...
    DDL("COMMIT;").execute(connection, table)
    # ... qui DOIT également être appelé !
    transaction.commit()

    # On supprime les tables temporaires.
    mapped_tables = metadata.tables.copy()
    del mapped_tables[tables.GroupPath.__tablename__]
    del mapped_tables[tables.UserSupItem.__tablename__]
    metadata.drop_all(tables=[
        tables.GroupPath.__table__,
        tables.UserSupItem.__table__
    ])
    metadata.drop_all(tables=mapped_tables.itervalues())

    transaction.commit()
    LOGGER.info(_("Temporary commit successful"))

    # On supprime l'infixe temporaire.
    configure.DB_BASENAME = configure.DB_BASENAME[:-4]
    settings['database']['db_basename'] = \
        settings['database']['db_basename'][:-4]

    # On bascule les traitements sur les tables finales.
    for table in metadata.sorted_tables:
        table.name = table.name[:base_len - 4] + table.name[base_len:]
        # Suppression du mot clé TEMPORARY. Ce n'est pas strictement
        # nécessaire car on ne recrée pas la table, mais au cas où...
        table._prefixes.pop(0)

