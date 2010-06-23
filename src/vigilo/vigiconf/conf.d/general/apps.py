apps = {
    'nagios-hls' : {
                   'priority' : 3,
                   'validationMethod' :  '',
                   'qualificationMethod' : './validation/nagios.sh',
                   'startMethod' : '/etc/init.d/nagios start',
                   'stopMethod' : '/etc/init.d/nagios stop ; (while : ; do pgrep nagios >/dev/null || break; sleep 1;done)'
                  },
    'nagios'    : { 
                   'priority' : 3,
                   'validationMethod' :  '',
                   'qualificationMethod' : './validation/nagios.sh',
                   'startMethod' : '/etc/init.d/nagios start',
                   'stopMethod' : '/etc/init.d/nagios stop ; (while : ; do pgrep nagios >/dev/null || break; sleep 1;done)'
                   },
    'corrtrap'    : { 
                   'priority' : 3,
                   'validationMethod' :  './validation/corrtrap.sh',
                   'qualificationMethod' : './validation/corrtrap.sh',
                   'startMethod' : '/etc/init.d/vigilo-corrtrap start',
                   'stopMethod' : '/etc/init.d/vigilo-corrtrap stop'
                   },
    'connector-metro': { 
                   'priority' : -1,
                   'validationMethod' :  './validation/connector-metro.sh',
                   'qualificationMethod' : './validation/connector-metro.sh',
                   'startMethod' : '/etc/init.d/vigilo-connector-metro reload',
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
    'rrdgraph'    : { 
                   'priority' : -1,
                   'validationMethod' :  './validation/rrdgraph.sh',
                   'qualificationMethod' : './validation/rrdgraph.sh',
                   'startMethod' : '/etc/init.d/httpd reload',
                   'stopMethod' : ''
                   },
}


appsByAppGroups = {
    'collect'           : ['nagios', 'collector', 'perfdata'],
    'metrology'         : ['connector-metro', 'rrdgraph'],
    'trap'              : ['corrtrap'],
    'correlation'       : ['nagios-hls'],
}


confid = "$Rev$"[6:-2]

# vim:set expandtab tabstop=4 shiftwidth=4:
