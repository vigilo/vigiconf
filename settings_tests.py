#import logging
#LOGGING_LEVELS = {
#    'vigilo.vigiconf': logging.DEBUG,
#}
LIBDIR = "/tmp"
CONFDIR = "src/vigilo/vigiconf/conf.d"
BASECONFDIR = "/tmp/vigiconf-conf"
LOCKFILE = "/tmp/vigiconf.lock"
SVNUSERNAME = "vigiconf"
SVNPASSWORD = "my_pass_word"
SVNREPOSITORY = ""
SIMULATE = True
SILENT = True

# sqlite db
VIGILO_MODELS_BDD_BASENAME = 'vigilo_'
VIGILO_ALL_DEFAULT_LANGUAGE = 'fr'
VIGILO_SQLALCHEMY = {
    'url': 'sqlite:///:memory:',
}
