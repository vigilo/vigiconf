# -*- coding: utf-8 -*-
################################################################################
#
# VigiConf
# Copyright (C) 2007-2010 CS-SI
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

"""
Ce module contient l'interface ligne de commande de VigiConf
"""

from __future__ import absolute_import

import fcntl
import sys
import os
import pwd
import atexit

import argparse
import gettext

from vigilo.common.conf import settings
settings.load_module(__name__)

from vigilo.models.configure import configure_db
configure_db(settings['database'], 'sqlalchemy_')

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate, translate_narrow
_ = translate(__name__)
N_ = translate_narrow(__name__)

from vigilo.common.conf import setup_plugins_path
setup_plugins_path(settings["vigiconf"].get("pluginsdir",
                   "/etc/vigilo/vigiconf/plugins"))

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib.exceptions import VigiConfError
from vigilo.vigiconf.lib.dispatchator import make_dispatchator

from xml.etree import ElementTree as ET # Python 2.5


def get_dispatchator(args, restrict=True):
    conf.load_general_conf()
    dispatchator = make_dispatchator()
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

def deploy(args):
    dispatchator = get_dispatchator(args)
    conf.load_xml_conf()
    if args.simulate:
        settings["vigiconf"]["simulate"] = True
        # pas de commit sur la base de données
        dispatchator.mode_db = 'no_commit'
    if args.force:
        dispatchator.force = True
    if args.revision:
        dispatchator.deploy_revision = args.revision
    stop_after = None
    if args.stop_after_generation:
        stop_after = "generation"
    if args.stop_after_push:
        stop_after = "deployment"
    dispatchator.run(stop_after=stop_after)

def apps(args):
    dispatchator = get_dispatchator(args)
    if args.stop or args.restart:
        dispatchator.apps_mgr.start_or_stop("stop")
    if args.start or args.restart:
        dispatchator.apps_mgr.start_or_stop("start")

#def undo(args):
#    args.revision = "PREV"
#    return deploy(args)
#    #dispatchator = get_dispatchator(args)
#    #dispatchator.undo()

def info(args):
    dispatchator = get_dispatchator(args)
    state = dispatchator.getState()
    encoding = sys.getfilesystemencoding() or "ISO-8859-1"
    encoding = encoding.lower()
    print "\n".join([s.encode(encoding) for s in state])

def discover(args):
    from vigilo.vigiconf.lib.confclasses.test import TestFactory
    from vigilo.vigiconf.discoverator import Discoverator, indent
    testfactory = TestFactory(confdir=settings["vigiconf"].get("confdir"))
    discoverator = Discoverator(testfactory, args.group)
    discoverator.testfactory.load_hclasses_checks()
    for target in args.target:
        if os.path.exists(target):
            discoverator.scanfile(target)
        else:
            discoverator.scanhost(target,
                                  args.community,
                                  args.version)
    discoverator.detect()
    elements = discoverator.declaration()
    indent(elements)
    print """<?xml version="1.0"?>"""
    print(ET.tostring(elements))

def server(args):
    dispatchator = get_dispatchator(args, restrict=False)
    conf.load_xml_conf() # les générateurs (nagios) en ont besoin
    dispatchator.server_status(args.server, args.status, args.no_deploy)


def parse_args():
    """Parses the commandline and starts the requested actions"""

    # @FIXME: permet de traduire les textes internes à argparse.
    N_('usage: ')
    N_('conflicting option string(s): %s')
    N_('subcommands')
    N_('unrecognized arguments: %s')
    N_('expected one argument')
    N_('expected at most one argument')
    N_('expected at least one argument')
    N_('expected %s argument(s)')
    N_('invalid choice: %r (choose from %s)')
    N_('positional arguments')
    N_('optional arguments')
    N_('too few arguments')
    N_('argument %s is required')
    N_('one of the arguments %s is required')
    N_('%s: error: %s\n')
    N_('show this help message and exit')
    N_("show program's version number and exit")

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
    parser_deploy.add_argument("--stop-after-generation", action="store_true",
                        help=N_("Stop the process after the file generation, "
                               "before pushing the files."))
    parser_deploy.add_argument("--stop-after-push", action="store_true",
                        help=N_("Stop after pushing the files to the remote "
                               "servers, and before restarting the services."))
    parser_deploy.add_argument("--revision", type=int,
                        help=N_("Deploy the given revision"))
    parser_deploy.add_argument("-f", "--force", action="store_true",
            dest="force", help=N_("Force the immediate execution of the "
                                  "command. Do not wait. Bypass all checks."))
    parser_deploy.add_argument("-n", "--dry-run", action="store_true",
                      dest="simulate", help=N_("Simulate only, no copy will "
                      "actually be made, no commit in the database."))
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

    return parser.parse_args()


def change_user(username="vigiconf", os=os, pwd=pwd):
    # pylint: disable-msg=W0621
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

def delete_lock(f):
    LOGGER.debug("Removing the lock.")
    fcntl.flock(f, fcntl.LOCK_UN)

def main():
    # Évite des problèmes d'accès aux fichiers ensuite
    # sur les machines durcies avec un UMASK en 077 (#324).
    os.umask(0022)

    # @FIXME: argparse utilise le domaine par défaut pour les traductions.
    # On définit explicitement le domaine par défaut ici. Ceci permet de
    # définir les traductions pour les textes de argparse dans VigiConf.
    gettext.textdomain('vigilo-vigiconf')
    args = parse_args()

    if args.debug:
        import logging
        LOGGER.parent.setLevel(logging.DEBUG)

    if not args.nochuid:
        change_user()

    LOGGER.debug("VigiConf starting...")
    f = open(settings["vigiconf"].get("lockfile",
        "/var/lock/vigilo-vigiconf/vigiconf.token"),'a+')
    try:
        LOGGER.debug("Acquiring the lock.")
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError, e:
        LOGGER.error(_("Can't obtain lock on lockfile (%(lockfile)s). "
                       "VigiConf already running ? REASON : %(error)s"),
                     { 'lockfile': f.name, 'error': e })
        sys.exit(1)

    # On veut être sûr que le verrou sera supprimé
    # à l'arrêt de vigiconf.
    atexit.register(delete_lock, f)

    try:
        args.func(args)
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
