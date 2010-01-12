CONFDIR = "/etc/vigilo-vigiconf/conf.d"
LIBDIR = "/var/lib/vigilo-vigiconf"
TARGETCONFDIR = "/etc/vigilo-vigiconf"
LOCKFILE = "/var/lock/vigilo-vigiconf/vigiconf.token"
SVNUSERNAME = "vigiconf"
SVNPASSWORD = "svnpass"
SVNREPOSITORY = "http://svnrepo/path/to/svn/repo"
SIMULATE = False
SILENT = False

# sqlite db
VIGILO_MODELS_BDD_BASENAME = 'vigilo_'
VIGILO_ALL_DEFAULT_LANGUAGE = 'fr'
VIGILO_SQLALCHEMY = {
    'url': 'sqlite:///:memory:',
}
