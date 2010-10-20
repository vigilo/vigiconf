appsGroupsByServer = {
    'interface' : {
        'P-F'             : ['localhost'],
        'Servers'         : ['localhost'],
        'Telecom'         : ['localhost'],
    },
    'collect' : {
        'P-F'             : ['localhost'],
        'Servers'         : ['localhost'],
        'Telecom'         : ['localhost'],
    },
    'metrology' : {
        'P-F'             : ['localhost'],
        'Servers'         : ['localhost'],
        'Telecom'         : ['localhost'],
    },
    'trap' : {
        'P-F'             : ['localhost'],
        'Servers'         : ['localhost'],
        'Telecom'         : ['localhost'],
    },
    'correlation' : {
        'P-F'             : ['localhost'],
        'Servers'         : ['localhost'],
        'Telecom'         : ['localhost'],
    },
}

# Permet de mettre les groupes d'hotes en mode copie pour les applications
# desirees. Consequence : tous les serveurs Vigilo de ce groupe seront
# equivalents (utile pour de la haute disponibilite)
#appsGroupsMode = {
#    'metrology' : {
#        'Servers'         : "duplicate",
#        'Telecom'         : "duplicate",
#    },
#}

# vim:set expandtab tabstop=4 shiftwidth=4:
