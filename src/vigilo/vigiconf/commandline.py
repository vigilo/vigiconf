#!/usr/bin/env python
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

import argparse

from vigilo.common.conf import settings
settings.load_module(__name__)

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.models.configure import configure_db
configure_db(settings['database'], 'sqlalchemy_',
    settings['database']['db_basename'])

from vigilo.common.gettext import translate
_ = translate(__name__)

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib.application import ApplicationError
from vigilo.vigiconf.dispatchator import DispatchatorError
from vigilo.vigiconf.lib import dispatchmodes


def get_dispatchator(args):
    from vigilo.models.session import metadata
    metadata.create_all()

    try:
        conf.loadConf()
    except Exception, e :
        LOGGER.error(_("Cannot load the configuration: %s"), e)
        sys.exit(1)
    dispatchator = dispatchmodes.getinstance()
    if args.server:
        try:
            dispatchator.restrict(args.server)
        except KeyError, e:
            # on pourrait utiliser la fonction "choices" de argparse, mais
            # ça obligerait à charger le dispatchator, et donc la conf,
            # dès le début même si on s'en sert pas
            LOGGER.error(_("ERROR: %s"), e.message)
            sys.exit(1)
    if not dispatchator.getServers():
        LOGGER.warning(_("No server to manage."))
    return dispatchator

def deploy(args):
    dispatchator = get_dispatchator(args)
    if (args.simulate):
        settings["vigiconf"]["simulate"] = True
        # pas de commit sur la base de données
        dispatchator.mode_db = 'no_commit'

    if (args.force):
        dispatchator.setModeForce(True)
    
    if (args.revision):
        dispatchator.deploy_revision = args.revision

    stop_after = None
    if args.stop_after_generation:
        stop_after = "generation"
    if args.stop_after_push:
        stop_after = "deployment"
    dispatchator.run(stop_after=stop_after)

def apps(args):
    dispatchator = get_dispatchator(args)
    if args.stop:
        dispatchator.stopApplications()
    elif args.start:
        dispatchator.startApplications()
    elif args.restart:
        dispatchator.restart()

def undo(args):
    dispatchator = get_dispatchator(args)
    dispatchator.undo()

def info(args):
    dispatchator = get_dispatchator(args)
    dispatchator.printState()

def discover(args):
    from .discoverator import Discoverator, DiscoveratorError, indent
    conf.loadConf()
    try:
        discoverator = Discoverator(options.group)
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
    except DiscoveratorError, e:
        sys.stderr.write(str(e)+"\n")
        sys.exit(1)

def parse_args():
    """Parses the commandline and starts the requested actions"""    

    parser = argparse.ArgumentParser(
                             description=_("Vigilo configuration manager"))
    parser.add_argument("--debug", action="store_true", help=_("Debug mode."))
    subparsers = parser.add_subparsers(dest='action', title=_("Subcommands"))

    # INFO
    parser_info = subparsers.add_parser("info", 
                      help="Prints a summary of the current configuration.")
    parser_info.set_defaults(func=info)
    parser_info.add_argument('server', nargs='*',
                      help=_("Servers to query, all of them if not specified."))

    # APPS
    parser_apps = subparsers.add_parser("apps",
                                    help=_("Application status management."))
    parser_apps.set_defaults(func=apps)
    group = parser_apps.add_mutually_exclusive_group(required=True)
    group.add_argument("--stop", action="store_true",
                       help=_("Stop the applications."))
    group.add_argument("--start", action="store_true",
                       help=_("Start the applications."))
    group.add_argument("--restart", action="store_true",
                       help=_("Restart the applications."))
    parser_apps.add_argument("applications", nargs="*",
                             help=_("Applications to manage, all of them "
                                    "if not specified."))
    # UNDO
    parser_undo = subparsers.add_parser("undo", 
                      help=_("Deploys the previously installed configuration. "
                             "2 consecutives undo will return to the "
                             "configuration that was installed before the "
                             "first undo (ie. redo)."))
    parser_undo.set_defaults(func=undo)
    parser_undo.add_argument("--no-restart", action="store_true",
                      help=_("Do not restart the applications after "
                             "switching the configuration."))
    parser_undo.add_argument('server', nargs='*',
                      help=_("Servers to undo, all of them if not specified."))

    # DEPLOY
    parser_deploy = subparsers.add_parser('deploy',
                        help=_("Deploys the configuration on each server "
                               "if the configuration has changed."))
    parser_deploy.set_defaults(func=deploy)
    parser_deploy.add_argument("--stop-after-generation", action="store_true",
                        help=_("Stop the process after the file generation, "
                               "before pushing the files."))
    parser_deploy.add_argument("--stop-after-push", action="store_true",
                        help=_("Stop after pushing the files to the remote "
                               "servers, and before restarting the services."))
    parser_deploy.add_argument("--revision", type=int,
                        help=_("Deploy the given revision"))
    parser_deploy.add_argument("-f", "--force", action="store_true", dest="force",
                      help=_("Force the immediate execution of the command. "
                            +"Do not wait. Bypass all checks."))
    parser_deploy.add_argument("-n", "--dry-run", action="store_true",
                      dest="simulate", help=_("Simulate only, no copy will "
                      "actually be made, no commit in the database."))
    parser_deploy.add_argument('server', nargs='*',
                      help=_("Servers to deploy to, all of them if "
                             "not specified."))

    # DISCOVER
    parser_discover = subparsers.add_parser('discover',
                          help=_("Discover the services available on a "
                                 "remote server"))
    parser_discover.set_defaults(func=discover)
    parser_discover.add_argument("-o", "--output",
                        type=argparse.FileType('w'), default=sys.stdout,
                        help=_("Output file. Default: standard output."))
    parser_discover.add_argument("-c", "--community", default="public",
                        help=_("SNMP community. Default: %(default)s."))
    parser_discover.add_argument("-v", "--version", default="2c",
                        help=_("SNMP version. Default: %(default)s."))
    parser_discover.add_argument("-g", "--group", default="Servers",
                        help=_("Main group. Default: %(default)s."))
    parser_discover.add_argument('target', nargs='+', type=list,
            help=_("Hosts or files to scan. The files must be the result "
                   "of an snmpwalk command on the '.1' OID with the "
                   "'-OnQ' options."))

    return parser.parse_args()


def main():
    args = parse_args()
    LOGGER.debug("VigiConf starting...")
    f = open(settings["vigiconf"].get("lockfile", "/var/lock/vigilo-vigiconf/vigiconf.token"),'a+')
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except Exception, exp:
        LOGGER.error("Can't obtain lock on lockfile. Dispatchator already "
                    +"running ? REASON : %s", exp)
        sys.exit(1)
    try:
        args.func(args)
    except (DispatchatorError, ApplicationError), e:
        LOGGER.exception(e)
    except Exception, e:
        if args.debug:
            LOGGER.exception(_("VigiConf error: %s"), str(e))
        else:
            LOGGER.error(_("VigiConf error: %s"), str(e))
        #for l in traceback.format_exc().split("\n"):
        #    LOGGER.error(l)
    LOGGER.debug("VigiConf ended.")


if __name__ == "__main__":
    main()
    #import cProfile
    #cProfile.run('main()', 'profiling')


# vim:set expandtab tabstop=4 shiftwidth=4:
