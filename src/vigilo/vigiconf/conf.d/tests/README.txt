In this folder, you can add test definitions, or override existing test
definitions. To do that, you need to copy the test you want to override,
preserving the directory structure, and change it.

Preserving the directory structure is very important: in this directory, there
can be only directories named after the host class, and then the tests:

    /etc/vigilo/vigiconf/conf.d/tests/<hostclass>/<Test>.py

When in doubt, remember that you must have the same directory structure as the
tests shipped with VigiConf.

