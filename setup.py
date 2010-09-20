#!/usr/bin/env python
# vim: set fileencoding=utf-8 sw=4 ts=4 et :
import os, sys
from glob import glob
from setuptools import setup, find_packages

sysconfdir = os.getenv("SYSCONFDIR", "/etc")
localstatedir = os.getenv("LOCALSTATEDIR", "/var")

tests_require = [
    'nose',
    'coverage',
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
                ["settings.ini", "src/vigilo/vigiconf/conf.d/README.source"]) )
    files.append((os.path.join(sysconfdir, "vigilo/vigiconf/ssh"), ["pkg/ssh_config"]))
    files.append(("/etc/cron.d", ["pkg/vigilo-vigiconf.cron"]))
    files.append((os.path.join(localstatedir, "lib/vigilo/vigiconf/deploy"), []))
    files.append((os.path.join(localstatedir, "lib/vigilo/vigiconf/revisions"), []))
    files.append((os.path.join(localstatedir, "lib/vigilo/vigiconf/tmp"), []))
    files.append((os.path.join(localstatedir, "lock/vigilo-vigiconf"), []))
    return files


setup(name='vigilo-vigiconf',
        version='2.0.0',
        author='Vigilo Team',
        author_email='contact@projet-vigilo.org',
        url='http://www.projet-vigilo.org/',
        description='vigilo configuration component',
        license='http://www.gnu.org/licenses/gpl-2.0.html',
        long_description='The Vigilo configuration system generates\n'
        +'configuration for every other component in Vigilo, distributes\n'
        +'it and restarts the services.\n',
        install_requires=[
            # dashes become underscores
            # order is important
            "setuptools",
            "argparse",
            "vigilo-common",
            "vigilo-models",
            ],
        extras_require={
            'tests': tests_require,
        },
        namespace_packages = [
            'vigilo',
        #    'vigilo.common',
            ],
        message_extractors={
            'src': [
                ('**.py', 'python', None),
            ],
        },
        packages=find_packages("src"),
        entry_points={
            'console_scripts': [
                'vigiconf = vigilo.vigiconf.commandline:main',
                'vigiconf-debug = vigilo.vigiconf.debug:main',
                ],
            'vigilo.vigiconf.applications': [
                'collector = vigilo.vigiconf.applications.collector:Collector',
                'connector-metro = vigilo.vigiconf.applications.connector_metro:ConnectorMetro',
                'corrtrap = vigilo.vigiconf.applications.corrtrap:CorrTrap',
                'nagios = vigilo.vigiconf.applications.nagios:Nagios',
                'nagios-hls = vigilo.vigiconf.applications.nagios_hls:NagiosHLS',
                'perfdata = vigilo.vigiconf.applications.perfdata:PerfData',
                'vigirrd = vigilo.vigiconf.applications.vigirrd:VigiRRD',
                'vigimap = vigilo.vigiconf.applications.vigimap:VigiMap',
                ],
            'vigilo.vigiconf.extensions': [
                'ventilator = vigilo.vigiconf.lib.ventilator:Ventilator',
                'server_remote = vigilo.vigiconf.lib.servertypes.remote:ServerRemote',
                'dispatchator_remote = vigilo.vigiconf.lib.dispatchmodes.remote:DispatchatorRemote',
                ],
            },
        package_dir={'': 'src'},
        #include_package_data = True,
        package_data={
            "vigilo.vigiconf": ["applications/*/*.sh", "applications/*/templates/*",
                                "validation/dtd/*.dtd", "validation/xsd/*.xsd",
                                "tests/*/*.py"],
            },
        data_files=get_data_files() +
            install_i18n("i18n", os.path.join(sys.prefix, 'share', 'locale')),
        )

#from pprint import pprint
#pprint(find_data_files("/etc/vigilo-vigiconf/conf.d", "src/vigilo/vigiconf/conf.d"))
