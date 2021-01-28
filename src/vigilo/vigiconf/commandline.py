# -*- coding: utf-8 -*-
# Copyright (C) 2007-2021 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Ce module contient l'interface ligne de commande de VigiConf
"""

from __future__ import absolute_import, print_function

import sys
import os
import pwd
import json
import argparse
import warnings
from pkg_resources import working_set

from vigilo.common.conf import settings
settings.load_module(__name__)

from vigilo.models.configure import configure_db
configure_db(settings['database'], 'sqlalchemy_')

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate, translate_narrow
_ = translate(__name__)
N_ = translate_narrow(__name__)

from vigilo.common.lock import grab_lock
from vigilo.common.argparse import prepare_argparse
from vigilo.common.conf import setup_plugins_path
setup_plugins_path(settings["vigiconf"].get("pluginsdir",
                   "/etc/vigilo/vigiconf/plugins"))

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib.exceptions import VigiConfError
from vigilo.vigiconf.lib.dispatchator import make_dispatchator

from xml.etree import ElementTree as ET # Python 2.5

class DeprecateStopAfterXAction(argparse._StoreConstAction):
    """
    Action de compatibilité pour les options C{--stop-after-generation}
    et C{--stop-after-push}.
    """

    def __call__(self, parser, namespace, values, option_string=None):
        """
        Effectue les mêmes opérations qu'une action "store_const",
        mais lève un avertissement concernant le fait que les options
        C{--stop-after-*} sont désormais obsolètes.
        """
        super(DeprecateStopAfterXAction, self).__call__(
            parser, namespace, values, option_string)
        if option_string:
            warnings.warn(DeprecationWarning((_(
                "%(option)s has been deprecated. Please use "
                "--stop-after=%(value)s instead.") % {
                    'option': option_string,
                    'value': option_string[13:],
                }).encode('utf-8')))

def flatten(lst):
    """
    Met à plat une liste. Cette fonctionne ne gère que les
    listes de listes (2 niveaux d'imbrication).
    """
    res = []
    for item in lst:
        if isinstance(item, list):
            res.extend(item)
        else:
            res.append(item)
    return res

def get_dispatchator(user, args, restrict=True):
    conf.load_general_conf(['general'])
    dispatchator = make_dispatchator(user, getattr(args, 'message', None))
    if restrict and args.server:
        try:
            dispatchator.restrict(args.server)
        except KeyError, e:
            # on pourrait utiliser la fonction "choices" de argparse, mais
            # ça obligerait à charger le dispatchator, et donc la conf,
            # dès le début même si on s'en sert pas
            LOGGER.error(_("ERROR: %s"), e.message)
            sys.exit(1)
    if not dispatchator.srv_mgr.servers:
        LOGGER.warning(_("No server to manage."))
    return dispatchator

def deploy(user, args):
    dispatchator = get_dispatchator(user, args)
    conf.load_xml_conf()
    if args.simulate:
        settings["vigiconf"]["simulate"] = True
        # pas de commit sur la base de données
        dispatchator.mode_db = 'no_commit'

    if args.revision:
        dispatchator.deploy_revision = args.revision
    dispatchator.force = tuple(flatten(args.force))
    dispatchator.run(stop_after=args.stop_after, with_dbonly=args.dbonly)

def apps(user, args):
    dispatchator = get_dispatchator(user, args)
    if args.stop or args.restart:
        dispatchator.apps_mgr.start_or_stop("stop")
    if args.start or args.restart:
        dispatchator.apps_mgr.start_or_stop("start")

#def undo(user, args):
#    args.revision = "PREV"
#    return deploy(user, args)
#    #dispatchator = get_dispatchator(user, args)
#    #dispatchator.undo()

def info(user, args):
    dispatchator = get_dispatchator(user, args)
    state = dispatchator.getState()
    encoding = sys.getfilesystemencoding() or "ISO-8859-1"
    encoding = encoding.lower()
    print("\n".join([s.encode(encoding) for s in state]))

def list_tests(user, args):
    from vigilo.vigiconf.lib.confclasses.test import TestFactory
    testfactory = TestFactory(confdir=settings["vigiconf"].get("confdir"))
    available_hclasses = sorted(testfactory.get_hclasses())
    if not args.classes:
        hclasses = available_hclasses
    else:
        hclasses = set()
        for hclass in args.classes:
            if hclass not in available_hclasses:
                LOGGER.warning(_("No such host class '%s'"), hclass)
            else:
                hclasses.add(hclass)

    for ep in working_set.iter_entry_points('vigilo.vigiconf.lib.testdumpers', args.format):
        func = ep.load()
        func(testfactory, hclasses, available_hclasses)
        sys.exit(0)
    else:
        LOGGER.error(_("Unknown format '%s'"), args.format)
        sys.exit(1)


def discover(user, args):
    from vigilo.vigiconf.lib.confclasses.test import TestFactory
    from vigilo.vigiconf.discoverator import Discoverator, indent
    from vigilo.vigiconf.discoverator import DiscoveratorError
    from vigilo.vigiconf.discoverator import SnmpwalkNotInstalled

    testfactory = TestFactory(confdir=settings["vigiconf"].get("confdir"))
    discoverator = Discoverator(testfactory, args.group)
    discoverator.testfactory.load_hclasses_checks()

    root = ET.Element("hosts")
    for target in args.target:
        try:
            discoverator.scan(target, args.community, args.version)
        except SnmpwalkNotInstalled:
            raise
        except DiscoveratorError, e:
            # On ne fait que logguer l'erreur pour générer quand même ce
            # qu'on a pu détecter jusqu'ici (cas du timeout)
            LOGGER.error(e.value)
        discoverator.detect(args.test)
        elements = discoverator.declaration()
        root.append(elements)
    indent(root)
    args.output.write(ET.tostring(root, encoding="utf8"))


def server(user, args):
    dispatchator = get_dispatchator(user, args, restrict=False)
    conf.load_xml_conf() # les générateurs (nagios) en ont besoin
    dispatchator.server_status(args.server, args.status, args.no_deploy)


def get_config(user, args):
    conf.load_general_conf(['general'])
    # @FIXME: Ce serait mieux de ne pas dupliquer du code de conf.py
    # Pour le moment, c'est difficilement évitable (les clés contenant
    # de la configuration ne sont pas exposées par conf.py).
    conf_keys = (
        'apps',
        'apps_conf',
        'confid',
        'appsGroupsByServer',
        'appsGroupsBackup',
    )
    dumpable_conf = {}
    for key in conf_keys:
        if hasattr(conf, key):
            dumpable_conf[key] = getattr(conf, key)
            # Le module "json" de Python ne peut pas dumper des set()
            # et on ne veut pas écrire un encodeur juste pour ça.
            if isinstance(dumpable_conf[key], set):
                dumpable_conf[key] = list(dumpable_conf[key])
    print(json.dumps(dumpable_conf, indent=2 if args.pretty else None))


def parse_args(): # pragma: no cover
    """Parses the commandline and starts the requested actions"""
    common_args_parser = argparse.ArgumentParser()
    common_args_parser.add_argument("--debug", action="store_true",
        help=N_("Debug mode."))
    common_args_parser.add_argument("--no-change-user", action="store_true",
        dest="nochuid", help=N_("Don't try to switch to the correct user."))

    parser = argparse.ArgumentParser(
                            add_help=False,
                            parents=[common_args_parser],
                            description=N_("Vigilo configuration manager"))
    subparsers = parser.add_subparsers(dest='action', title=N_("Subcommands"))

    # INFO
    parser_info = subparsers.add_parser("info",
                    add_help=False,
                    parents=[common_args_parser],
                    help=N_("Prints a summary of the current configuration."))
    parser_info.set_defaults(func=info)
    parser_info.add_argument('server', nargs='*',
                    help=N_("Supervision servers to query, all of them if "
                            "not specified."))

    # LIST-TESTS
    supported_formats = set()
    for ep in working_set.iter_entry_points('vigilo.vigiconf.lib.testdumpers'):
        try:
            ep.load()
            supported_formats.add(ep.name)
        except:
            pass
    parser_list_tests = subparsers.add_parser("list-tests",
                    add_help=False,
                    parents=[common_args_parser],
                    help=N_("Lists tests available for certain host classes."))
    parser_list_tests.add_argument('classes', nargs='*',
                    help=N_("Host classes to query."))
    parser_list_tests.add_argument("--format", choices=sorted(supported_formats),
                        default='text', help=N_("Set the output format."))
    parser_list_tests.set_defaults(func=list_tests)

    # @deprecated: la commande 'apps' n'est pas utilisée en v2
    # et correspond surtout à du debugging (reste de la v1).
    # Le code derrière est probablement obsolète à présent.

#    # APPS
#    parser_apps = subparsers.add_parser("apps",
#                    add_help=False,
#                    parents=[common_args_parser],
#                    help=N_("Application status management."))
#    parser_apps.set_defaults(func=apps)
#    group = parser_apps.add_mutually_exclusive_group(required=True)
#    group.add_argument("--stop", action="store_true",
#                       help=N_("Stop the applications."))
#    group.add_argument("--start", action="store_true",
#                       help=N_("Start the applications."))
#    group.add_argument("--restart", action="store_true",
#                       help=N_("Restart the applications."))
#    parser_apps.add_argument("applications", nargs="*",
#                             help=N_("Applications to manage, all of them "
#                                    "if not specified."))

    ## UNDO
    #parser_undo = subparsers.add_parser("undo",
    #                add_help=False,
    #                parents=[common_args_parser],
    #                help=N_("Deploys the previously installed configuration. "
    #                         "2 consecutives undo will return to the "
    #                         "configuration that was installed before the "
    #                         "first undo (ie. redo)."))
    #parser_undo.set_defaults(func=undo)
    #parser_undo.add_argument("--no-restart", action="store_true",
    #                  help=N_("Do not restart the applications after "
    #                         "switching the configuration."))
    #parser_undo.add_argument('server', nargs='*',
    #                  help=N_("Supervision servers to undo, all of them if "
    #                        "not specified."))

    # DEPLOY
    parser_deploy = subparsers.add_parser('deploy',
                        add_help=False,
                        parents=[common_args_parser],
                        help=N_("Deploys the configuration on each server "
                               "if the configuration has changed."))
    parser_deploy.set_defaults(func=deploy)
    parser_deploy.add_argument("--stop-after-generation",
                        action=DeprecateStopAfterXAction,
                        dest="stop_after", const="generation",
                        help=N_("[DEPRECATED] Stop the process after "
                                "the file generation, before pushing "
                                "the files."))
    parser_deploy.add_argument("--stop-after-push",
                        action=DeprecateStopAfterXAction,
                        dest="stop_after", const="push",
                        help=N_("[DEPRECATED] Stop after pushing the files "
                                "to the remote servers, before services are "
                                "restarted."))
    stop_after_choices = ['generation', 'push']
    parser_deploy.add_argument("--stop-after", dest="stop_after", default=None,
                        choices=stop_after_choices, metavar=N_("OPERATION"),
                        help=N_("Stop after the given OPERATION (one of '%s')")
                            % "', '".join(stop_after_choices))
    parser_deploy.add_argument("--revision", type=int,
                        help=N_("Deploy the given revision"))
    force_choices = ['deploy', 'db-sync']
    parser_deploy.add_argument("-f", "--force", action="append",
                        dest="force", nargs='?', choices=force_choices,
                        default=[], const=force_choices,
                        help=N_("Force the given operations. This can be used "
                                "to return VigiConf to a known good state."))
    parser_deploy.add_argument("-m", "--message", default=None,
                        help=N_("Add a reason/description for this deployment."))
    parser_deploy.add_argument("-n", "--dry-run", action="store_true",
                        dest="simulate",
                        help=N_("Simulate only, no copy will "
                                "actually be made, no commit in the database."))
    parser_deploy.add_argument("--no-dbonly", action="store_false",
                        dest="dbonly",
                        help=N_("Disable generators marked as requiring only "
                                "the database to operate (dbonly)."))
    parser_deploy.add_argument('server', nargs='*',
                      help=N_("Supervision servers to deploy to, all of them "
                             "if not specified."))

    # DISCOVER
    parser_discover = subparsers.add_parser('discover',
                        add_help=False,
                        parents=[common_args_parser],
                        help=N_("Discover the services available on a "
                                 "remote server."))
    parser_discover.set_defaults(func=discover)
    parser_discover.add_argument("-o", "--output",
                        type=argparse.FileType('w'), default=sys.stdout,
                        help=N_("Output file. Default: standard output."))
    parser_discover.add_argument("-c", "--community", default="public",
                        help=N_("SNMP community. Default: %(default)s."))
    parser_discover.add_argument("-v", "--version", default="2c",
                        help=N_("SNMP version. Default: %(default)s."))
    parser_discover.add_argument("-g", "--group", default="Servers",
                        help=N_("Main group. Default: %(default)s."))
    parser_discover.add_argument("-t", "--test", default=[], action="append",
                        help=N_("Tests to check."))
    parser_discover.add_argument('target', nargs='+',
            help=N_("Hosts or files to scan. The files must be the result "
                   "of an snmpwalk command on the '.1' OID with the "
                   "'-OnQe' options."))

    # server-status
    parser_server = subparsers.add_parser('server-status',
                        add_help=False,
                        parents=[common_args_parser],
                        help=N_("Enables or disables a Vigilo server"))
    parser_server.set_defaults(func=server)
    parser_server.add_argument("-n", "--no-deploy", action="store_true",
                        help=N_("Don't re-deploy the configuration, "
                                "only set the status."))
    parser_server.add_argument("status", choices=["enable", "disable"],
                               help=N_("New status"))
    parser_server.add_argument("server", nargs="+",
                               help=N_("Server name(s) to enable/disable"))

    # get-config
    parser_config = subparsers.add_parser('get-config',
                        add_help=False,
                        parents=[common_args_parser],
                        help=N_("Retrieve various information about VigiConf's configuration"))
    parser_config.add_argument("-p", "--pretty", action="store_true",
                        default=False,
                        help=N_("Output the configuration in a pretty way."))
    parser_config.set_defaults(func=get_config)

    return parser.parse_args()


def change_user(username="vigiconf"): # pragma: no cover
    # Ne pas remonter les deux imports suivants, nécessaires pour les tests
    # unitaires (mock)
    # pylint: disable-msg=W0621,W0404
    import os, pwd

    uid = os.getuid()
    # Vigiconf est lancé en tant que "root",
    # on bascule sur un compte utilisateur
    # plus approprié (vigiconf).
    if not uid:
        LOGGER.warning(_("VigiConf was launched as user 'root'. "
                        "Switching to user '%s' instead."), username)
        try:
            entry = pwd.getpwnam(username)
        except KeyError:
            LOGGER.error(_("Unable to switch to user '%s'. Aborting."),
                         username)
            sys.exit(2)

        # On remplace les UID/GID réels et effectifs
        # par ceux de l'utilisateur 'vigiconf', ainsi que les variables
        # d'environnements nécessaires.
        os.setregid(entry.pw_gid, entry.pw_gid)

        # Permet de charger les groupes supplémentaires
        # associés à l'utilisateur "vigiconf".
        if hasattr(os, "initgroups"):
            os.initgroups(username, entry.pw_gid) #pylint: disable-msg=E1103
        else:
            import initgroups
            initgroups.initgroups(username, entry.pw_gid)

        os.setreuid(entry.pw_uid, entry.pw_uid)
        os.environ["LOGNAME"] = entry.pw_name
        os.environ["USER"] = entry.pw_name
        os.environ["USERNAME"] = entry.pw_name
        os.environ["HOME"] = entry.pw_dir
        os.environ["SHELL"] = entry.pw_shell

    if pwd.getpwuid(os.getuid()).pw_name != username:
        LOGGER.error(_("VigiConf was not launched as user '%s'. "
                       "Aborting."), username)
        sys.exit(2)

def main(): # pragma: no cover
    # Évite des problèmes d'accès aux fichiers ensuite
    # sur les machines durcies avec un UMASK en 077 (#324).
    os.umask(0022)

    prepare_argparse()
    args = parse_args()

    if args.debug:
        import logging
        LOGGER.parent.setLevel(logging.DEBUG)

    # On mémorise l'identité de l'utilisateur ayant exécuté VigiConf,
    # pour pouvoir assurer la traçabilité plus tard.
    try:
        uid = os.getuid()
        user = pwd.getpwuid(uid).pw_name
        # Si la commande semble avoir été exécutée via "sudo",
        # on récupère l'identité de l'utilisateur initial.
        if uid == 0 and os.environ.get('SUDO_USER'):
            user = os.environ['SUDO_USER']
    except:
        user = None

    # Pour la commande discover, on ne change pas d'utilisateur
    # pour éviter une erreur lorsque le fichier de destination
    # n'est pas accessible par l'utilisateur "vigiconf" (cf. #705).
    if args.func != discover and not args.nochuid:
        change_user()

    # Pour les commandes basiques qui ne font pas d'écritures,
    # il n'est pas nécessaire de poser un verrou.
    if args.func not in (list_tests, discover, get_config):
        lockfile = settings["vigiconf"].get("lockfile",
                            "/var/lock/subsys/vigilo-vigiconf/vigiconf.token")
        lock_result = grab_lock(lockfile)
        if not lock_result:
            sys.exit(1)

    LOGGER.debug("VigiConf starting...")
    try:
        args.func(user, args)
    except VigiConfError, e:
        if args.debug:
            LOGGER.exception(_("VigiConf error: %s"), e.value)
        else:
            LOGGER.error(_("VigiConf error: %s"), e.value)
        sys.exit(1)
        #for l in traceback.format_exc().split("\n"):
        #    LOGGER.error(l)
    LOGGER.info(_("VigiConf is done."))


if __name__ == "__main__":
    main()
    #import cProfile
    #cProfile.run('main()', 'profiling')


# vim:set expandtab tabstop=4 shiftwidth=4:
