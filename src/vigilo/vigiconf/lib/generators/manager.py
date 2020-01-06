# -*- coding: utf-8 -*-
# Copyright (C) 2007-2020 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>
"""
Generators for the Vigilo Config Manager
"""

from __future__ import absolute_import

import os
import os.path
import shutil
import multiprocessing
import sys
from traceback import format_tb

import transaction

from vigilo.common.conf import settings
settings.load_module(__name__)

from vigilo.models.configure import configure_db
configure_db(settings['database'], 'sqlalchemy_')

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib import VigiConfError
from vigilo.vigiconf.lib.generators.base import SkipGenerator
from vigilo.vigiconf.lib.validator import Validator
from vigilo.vigiconf.lib.ventilation import get_ventilator
from vigilo.vigiconf.lib.loaders.manager import LoaderManager


class GenerationError(VigiConfError):
    """
    Exception remontée quand il y a eu une erreur à la génération
    """
    pass


class GeneratorManager(object):
    """
    Handles the generator library.
    @cvar apps: the list of available applications.
    @type apps: C{list}
    """

    genshi_enabled = False

    def __init__(self, apps):
        self.apps = apps
        self.ventilator = None
        try:
            self.genshi_enabled = settings['vigiconf'].as_bool(
                                    'enable_genshi_generation')
        except KeyError:
            self.genshi_enabled = False
        self._ventilation = None

    def run_all_generators(self, validator):
        """
        Execute la méthode I{generate()} de la classe pointée par l'attribut
        I{generate} de chaque application
        """
        vba = self.ventilator.ventilation_by_appname(self._ventilation)
        LOGGER.debug("Generating configuration")
        results = {}
        for app in self.apps:
            # d'abord on indique à l'application les serveurs où déployer
            for srv in self.ventilator.servers_for_app(self._ventilation, app):
                app.add_server(srv)
            if not app.generator:
                continue
            validator.addAGenerator()
            if app.dbonly:
                continue # sera fait après le déploiement
            generator = app.generator(app, vba)
            try:
                generator.generate()
            except SkipGenerator as e:
                LOGGER.warning(e)
                LOGGER.warning(_("Skipping %s generator"), app.name)
            else:
                generator.write_scripts()
                LOGGER.info(_("Generated configuration for %s"), app.name)
                results[app.name] = generator.results
        for appname, result_data in results.items():
            for element, msg in result_data.get("errors", []):
                validator.addError(appname, element, msg)
            for element, msg in result_data.get("warnings", []):
                validator.addWarning(appname, element, msg)
            if "files" in result_data:
                validator.addFiles(result_data["files"])
            if "dirs" in result_data:
                validator.addDirs(result_data["dirs"])
        LOGGER.debug("Configuration generated")

    def generate(self, rev_mgr, nosyncdb=False):
        """
        Méthode principale de la classe, qui charge les données en base et
        génère les fichiers de configuration.
        @param nosyncdb: si cet argument est vrai, on essaye pas de
            synchroniser la configuration du disque avec la base de données
        @type nosyncdb: C{boolean}
        @raise L{GenerationError}
        """
        validator = Validator()
        loader = LoaderManager(rev_mgr)
        return self._generate(loader, validator, nosyncdb)

    def _generate(self, loader, validator, nosyncdb=False):
        gendir = os.path.join(settings["vigiconf"].get("libdir"), "deploy")
        shutil.rmtree(gendir, ignore_errors=True)
        if not nosyncdb:
            LOGGER.debug("Syncing with database")
            loader.load_apps_db(self.apps)
            loader.load_conf_db()
            loader.load_vigilo_servers_db()
        LOGGER.info(_("Computing ventilation"))
        self.ventilator = get_ventilator(self.apps)
        self._ventilation = self.ventilator.ventilate()
        LOGGER.debug("Loading ventilation in DB")
        loader.load_ventilation_db(self._ventilation, self.apps)

        LOGGER.debug("Validating ventilation")
        validator.ventilation = self._ventilation
        if not validator.preValidate():
            for errmsg in validator.getSummary(details=True, stats=True):
                LOGGER.error(errmsg)
            raise GenerationError("prevalidation")

        LOGGER.info(_("Running generators"))
        self.run_all_generators(validator)

        if validator.hasErrors():
            for errmsg in validator.getSummary(details=True, stats=True):
                LOGGER.error(errmsg)
            raise GenerationError("validation")
        for msg in validator.getSummary(details=True, stats=True):
            LOGGER.info(msg)

    def generate_dbonly(self):
        """
        Execute la méthode I{generate()} de la classe pointée par l'attribut
        I{generate} de chaque application à condition qu'elle ait C{dbonly} à True
        """
        db_generators = [ app for app in self.apps
                          if app.dbonly and app.generator ]
        if not db_generators:
            return
        if len(db_generators) == 1:
            # pas besoin de multiprocessing
            app = db_generators[0]
            LOGGER.info(_("Generating configuration for %s"), app.name)
            generator = app.generator(app, {})
            try:
                generator.generate()
            except SkipGenerator as e:
                transaction.abort()
                LOGGER.warning(e)
                LOGGER.warning(_("Skipping %s generator"), app.name)
            else:
                transaction.commit()
            return
        # Ici, on a plusieurs générateurs DB, à exécuter en parallèle
        LOGGER.info(_("Running database generators"))
        pool = multiprocessing.Pool(len(db_generators))
        results = {}
        for app in db_generators:
            results[app.name] = pool.apply_async(_run_db_generator,
                                                 (app.__class__, ))
        errors = {}
        for appname, result in results.items():
            try:
                result.get()
            except Exception: # pylint: disable-msg=W0703
                errors[appname] = sys.exc_info()
        for appname, error in errors.items():
            errtype, err, tb = error
            LOGGER.error(_("%(errtype)s in application %(app)s: %(error)s"),
                         {"app": appname, "error": str(err),
                          "errtype": errtype.__name__})
            LOGGER.debug("".join(format_tb(tb)))
            del tb
        pool.close()
        pool.join()
        LOGGER.debug("Database configuration generated")

    def _choose_metro_server(self, hostname, vba): # pylint: disable-msg=R0201
        """On choisit le même serveur que nagios si possible"""
        nagios_servers = vba[hostname]["nagios"]
        if not isinstance(nagios_servers, list):
            nagios_servers = [nagios_servers, ]
        for metro_server in vba[hostname]["connector-metro"]:
            if metro_server in nagios_servers:
                return metro_server
        return vba[hostname]["connector-metro"][0]


def _run_db_generator(appclass):
    from vigilo.models.session import DBSession
    # Pour éviter que le pool loggue les déconnexions (SALE)
    #DBSession.bind.pool._should_log_info = False
    # On force la reconnection à la base de données
    DBSession.bind.dispose()
    transaction.begin()

    app = appclass()
    generator = app.generator(app, {})
    try:
        generator.generate()
    except SkipGenerator as e:
        LOGGER.warning(e)
        LOGGER.warning(_("Skipping %s generator"), app.name)
        transaction.abort()
    else:
        transaction.commit()
        LOGGER.info(_("Generated configuration for %s"), app.name)
    finally:
        DBSession.close_all()
        # fermeture propre des connexions, ce sous-process va être tué
        DBSession.bind.dispose()
