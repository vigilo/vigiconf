#!/usr/bin/env python
# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2019 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

import os, sys
from platform import python_version_tuple
from glob import glob
from setuptools import setup, find_packages

sysconfdir = os.getenv("SYSCONFDIR", "/etc")
localstatedir = os.getenv("LOCALSTATEDIR", "/var")
cronext = os.getenv("CRONEXT", ".cron")

install_requires=[
    # order is important
    "setuptools",
    "lxml",
    "vigilo-common",
    "vigilo-models",
    "networkx",
    "netifaces",
    ]
if tuple(python_version_tuple()) < ('2', '6'):
    install_requires.append("multiprocessing")
if tuple(python_version_tuple()) < ('2', '7'):
    install_requires.append("initgroups")
    install_requires.append("argparse")
    install_requires.append("ordereddict")

tests_require = [
    'coverage',
    'nose',
    'pylint',
    'mock',
]

def install_i18n(i18ndir, destdir):
    data_files = []
    langs = []
    for f in os.listdir(i18ndir):
        if os.path.isdir(os.path.join(i18ndir, f)) and not f.startswith("."):
            langs.append(f)
    for lang in langs:
        for f in os.listdir(os.path.join(i18ndir, lang, "LC_MESSAGES")):
            if f.endswith(".mo"):
                data_files.append(
                        (os.path.join(destdir, lang, "LC_MESSAGES"),
                         [os.path.join(i18ndir, lang, "LC_MESSAGES", f)])
                )
    return data_files

def find_data_files(basedir, srcdir):
    data_files = []
    for root, dirs, files in os.walk(srcdir):
        if '.svn' in dirs:
            dirs.remove('.svn')  # don't visit SCM directories
        if not files:
            continue
        subdir = root.replace(srcdir, "")
        if subdir.startswith("/"):
            subdir = subdir[1:]
        data_files.append( (os.path.join(basedir, subdir),
                           [os.path.join(root, name) for name in files]) )
    return data_files

def get_data_files():
    files = find_data_files(
                os.path.join(sysconfdir, "vigilo/vigiconf/conf.d.example"),
                "src/vigilo/vigiconf/conf.d")
    # filter those out
    files = [f for f in files if f[0] != "/etc/vigilo/vigiconf/conf.d.example/"]
    # others
    files.append( (os.path.join(sysconfdir, "vigilo/vigiconf/conf.d"), []) )
    files.append( (os.path.join(sysconfdir, "vigilo/vigiconf"),
                ["settings.ini", "src/vigilo/vigiconf/conf.d/README.post-install"]) )
    files.append( (os.path.join(sysconfdir, "vigilo/vigiconf/plugins"), []) )
    files.append((os.path.join(sysconfdir, 'cron.d'), ["pkg/vigilo-vigiconf%s" % cronext]))
    files.append((os.path.join(localstatedir, "lib/vigilo/vigiconf/deploy"), []))
    files.append((os.path.join(localstatedir, "lib/vigilo/vigiconf/revisions"), []))
    files.append((os.path.join(localstatedir, "lib/vigilo/vigiconf/tmp"), []))
    files.append((os.path.join(localstatedir, "lock/subsys"), []))
    files.append((os.path.join(localstatedir, "lock/subsys/vigilo-vigiconf"), []))
    return files


setup(name='vigilo-vigiconf',
        version='5.1.0b1',
        author='Vigilo Team',
        author_email='contact.vigilo@c-s.fr',
        url='https://www.vigilo-nms.com/',
        license='http://www.gnu.org/licenses/gpl-2.0.html',
        description="Configuration manager for the supervision system",
        long_description="This program generates and pushes the "
                         "configuration for the applications used in Vigilo.",
        zip_safe=False,
        install_requires=install_requires,
        namespace_packages=['vigilo'],
        packages=find_packages("src"),
        message_extractors={
            'src': [
                ('**.py', 'python', None),
            ],
        },
        extras_require={
            'tests': tests_require,
        },
        entry_points={
            'console_scripts': [
                'vigiconf = vigilo.vigiconf.commandline:main',
                'vigiconf-migrate = vigilo.vigiconf.migrate_tests_5_0_0:main',
                ],
            'vigilo.vigiconf.lib.testdumpers': [
                'text = vigilo.vigiconf.lib.testdumpers.text:dump',
                'json = vigilo.vigiconf.lib.testdumpers.json:dump',
            ],
            'vigilo.vigiconf.applications': [
                'collector = vigilo.vigiconf.applications.collector:Collector',
                'connector-metro = vigilo.vigiconf.applications.connector_metro:ConnectorMetro',
                'nagios = vigilo.vigiconf.applications.nagios:Nagios',
                'perfdata = vigilo.vigiconf.applications.perfdata:PerfData',
                'vigirrd = vigilo.vigiconf.applications.vigirrd:VigiRRD',
                ],
            'vigilo.vigiconf.testlib': [
                'vigiconf-default = vigilo.vigiconf.tests',
                ],
        },
        package_dir={'': 'src'},
        include_package_data = True,
        data_files=get_data_files() +
            install_i18n("i18n", os.path.join(sys.prefix, 'share', 'locale')),
        )
