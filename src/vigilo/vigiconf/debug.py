#!/usr/bin/python

"""
This module is used to test the different parts of VigiConf
"""

from __future__ import absolute_import

from vigilo.common.conf import settings

import sys
import os

def main():
    if len(sys.argv) != 2:
        print "Usage: debug.py <module>"
        sys.exit(2)

    os.environ["VIGICONF_MAINCONF"] = os.path.join(
                                    os.path.abspath(os.path.dirname(__file__)),
                                    "vigiconf-test.conf")

    module = sys.argv[1]

    if module == "conf":
        from . import conf
        import pprint
        conf.loadConf()
        print "hostsConf="
        pprint.pprint(conf.hostsConf)
        print "groupsHierarchy="
        pprint.pprint(conf.groupsHierarchy)
        print "dependencies="
        pprint.pprint(conf.dependencies)
        print "dynamic groups="
        pprint.pprint(conf.dynamicGroups)

    elif module == "generator":
        from . import conf
        from . import generator
        conf.loadConf()
        _gendir = os.path.join(settings["vigiconf"].get("libdir"), "deploy")
        os.system("rm -rf %s/*" % _gendir)
        if 0:
            import hotshot, hotshot.stats
            _prof = hotshot.Profile("/tmp/generator.prof")
            _prof.runcall(generator.generate, _gendir)
            _prof.close()
            _stats = hotshot.stats.load("/tmp/generator.prof")
            _stats.strip_dirs()
            _stats.sort_stats('time', 'calls')
            _stats.print_stats(20)
        else:
            if not generator.generate(_gendir):
                sys.exit(1)

if __name__ == "__main__":
    main()
