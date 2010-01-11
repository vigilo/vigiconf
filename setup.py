#!/usr/bin/env python
# vim: set fileencoding=utf-8 sw=4 ts=4 et :
import os
from glob import glob
from setuptools import setup, find_packages


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
            'coverage',
            'nose',
            'pylint',
            'SQLAlchemy',
            "vigilo-common",
            "psycopg2",
            "vigilo-models",
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
            "vigilo.vigiconf": ["validation/*.sh", "validation/dtd/*.dtd", "tests/*/*.py"],
            },
        data_files=find_data_files("/etc/vigilo-vigiconf/conf.d",
                                   "src/vigilo/vigiconf/conf.d"),
        )

#from pprint import pprint
#pprint(find_data_files("/etc/vigilo-vigiconf/conf.d", "src/vigilo/vigiconf/conf.d"))
