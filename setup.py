#!/usr/bin/env python
# vim: set fileencoding=utf-8 sw=4 ts=4 et :
import os
from glob import glob
from setuptools import setup, find_packages

sysconfdir = os.getenv("SYSCONFDIR", "/etc")
localstatedir = os.getenv("LOCALSTATEDIR", "/var")


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
    for d in ["conf.d", "new", "prod"]:
        files.append( (os.path.join(sysconfdir, "vigilo/vigiconf", d), []) )
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
        version='0.1',
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
            'SQLAlchemy',
            "vigilo-common",
            "psycopg2",
            "vigilo-models",
            "vigilo-turbogears"
            ],
        namespace_packages = [
            'vigilo',
        #    'vigilo.common',
            ],
        packages=find_packages("src"),
        #[
        #    'vigilo',
        #    'vigilo.common',
        #    'vigilo.vigiconf',
        #    ],
        entry_points={
            'console_scripts': [
                'vigiconf-dispatchator = vigilo.vigiconf.dispatchator:main',
                'vigiconf-discoverator = vigilo.vigiconf.discoverator:main',
                'vigiconf-debug = vigilo.vigiconf.debug:main',
                ],
            },
        package_dir={'': 'src'},
        #include_package_data = True,
        package_data={
            "vigilo.vigiconf": ["validation/*.sh", "validation/dtd/*.dtd",
                                "validation/xsd/*.xsd", "tests/*/*.py"],
            },
        data_files=get_data_files(),
        )

#from pprint import pprint
#pprint(find_data_files("/etc/vigilo-vigiconf/conf.d", "src/vigilo/vigiconf/conf.d"))
