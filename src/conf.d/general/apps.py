apps = {
    'nagios'    : { 
                   'priority' : 3,
                   'validationMethod' :  '',
                   'qualificationMethod' : './validation/nagios.sh',
                   'startMethod' : '/etc/init.d/nagios3 start',
                   'stopMethod' : '/etc/init.d/nagios3 stop ; (while : ; do pgrep nagios3 >/dev/null || break; sleep 1;done)'
                   },
    'corrtrap'    : { 
                   'priority' : 3,
                   'validationMethod' :  './validation/corrtrap.sh',
                   'qualificationMethod' : './validation/corrtrap.sh',
                   'startMethod' : '/etc/init.d/vigilo-corrtrap start',
                   'stopMethod' : '/etc/init.d/vigilo-corrtrap stop'
                   },
    'storeme'    : { 
                   'priority' : -1,
                   'validationMethod' :  './validation/storeme.sh',
                   'qualificationMethod' : './validation/storeme.sh',
                   'startMethod' : '',
                   'stopMethod' : ''
                   },
    'corrsup'    : { 
                   'priority' : 2,
                   'validationMethod' :  '',
                   'qualificationMethod' : './validation/corrsup.sh',
                   'startMethod' : '/etc/init.d/vigilo-corrsup start',
                   'stopMethod' : '/etc/init.d/vigilo-corrsup stop'
                   },
    'dns1'    : { 
                   'priority' : 1,
                   'validationMethod' :  '',
                   'qualificationMethod' : '',
                   'startMethod' : '/etc/init.d/bind9 reload',
                   'stopMethod' : ''
                   },
    'dns2'    : { 
                   'priority' : 1,
                   'validationMethod' :  '',
                   'qualificationMethod' : '',
                   'startMethod' : '/etc/init.d/bind9 reload',
                   'stopMethod' : ''
                   },
    'apacheRP'    : { 
                   'priority' : -1,
                   'validationMethod' :  '',
                   'qualificationMethod' : '',
                   'startMethod' : '/etc/init.d/apache2 reload',
                   'stopMethod' : ''
                   },
    'collector'    : { 
                   'priority' : -1,
                   'validationMethod' :  './validation/collector.sh',
                   'qualificationMethod' : './validation/collector.sh',
                   'startMethod' : '',
                   'stopMethod' : ''
                   },
    'perfdata'    : { 
                   'priority' : -1,
                   'validationMethod' :  './validation/perfdata.sh',
                   'qualificationMethod' : './validation/perfdata.sh',
                   'startMethod' : '',
                   'stopMethod' : ''
                   },
    'supnav'    : { 
                   'priority' : -1,
                   'validationMethod' :  './validation/supnav.sh',
                   'qualificationMethod' : './validation/supnav.sh',
                   'startMethod' : '',
                   'stopMethod' : ''
                   },
    'nagvis'    : { 
                   'priority' : -1,
                   'validationMethod' :  './validation/nagvis.sh',
                   'qualificationMethod' : './validation/nagvis.sh',
                   'startMethod' : '',
                   'stopMethod' : ''
                   },
    'rrdgraph'    : { 
                   'priority' : -1,
                   'validationMethod' :  './validation/rrdgraph.sh',
                   'qualificationMethod' : './validation/rrdgraph.sh',
                   'startMethod' : '/etc/init.d/apache2 reload',
                   'stopMethod' : ''
                   },
    'reportingv2' : {
                   'priority' : -1,
                   'validationMethod' :  '',
                   'qualificationMethod' : '',
                   'startMethod' : '',
                   'stopMethod' : ''
                   },
    'dashboard_db'    : { 
                   'priority' : -1,
                   'validationMethod' :  '',
                   'qualificationMethod' : '',
                   'startMethod' : 'mysql < /etc/confmgr/prod/dashboard_db/dashboard_db.sql',
                   'stopMethod' : ''
                   },
}


appsByAppGroups = {
    'collect'           : ['nagios','collector','perfdata'],
    'metrology'         : ['storeme','rrdgraph'],
    'corrpres'          : ['corrsup','supnav','apacheRP','nagvis','dashboard_db'],
    'reporting'         : ['reportingv2'],
    'secu'              : [],
    'trap'              : ['corrtrap'],
    'dns1'              : ['dns1'],
    'dns2'              : ['dns2'],
}


# vim:set expandtab tabstop=4 shiftwidth=4:
