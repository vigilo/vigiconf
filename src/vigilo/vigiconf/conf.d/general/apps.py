apps = {
    u'nagios'    : { 
                   u'priority' : 3,
                   u'validationMethod' :  '',
                   u'qualificationMethod' : './validation/nagios.sh',
                   u'startMethod' : '/etc/init.d/nagios start',
                   u'stopMethod' : '/etc/init.d/nagios stop ; (while : ; do pgrep nagios >/dev/null || break; sleep 1;done)'
                   },
    u'corrtrap'    : { 
                   u'priority' : 3,
                   u'validationMethod' :  './validation/corrtrap.sh',
                   u'qualificationMethod' : './validation/corrtrap.sh',
                   u'startMethod' : '/etc/init.d/vigilo-corrtrap start',
                   u'stopMethod' : '/etc/init.d/vigilo-corrtrap stop'
                   },
    u'connector-metro': { 
                   u'priority' : -1,
                   u'validationMethod' :  './validation/connector-metro.sh',
                   u'qualificationMethod' : './validation/connector-metro.sh',
                   u'startMethod' : '',
                   u'stopMethod' : ''
                   },
    u'apacheRP'    : { 
                   u'priority' : -1,
                   u'validationMethod' :  '',
                   u'qualificationMethod' : '',
                   u'startMethod' : '/etc/init.d/httpd reload',
                   u'stopMethod' : ''
                   },
    u'collector'    : { 
                   u'priority' : -1,
                   u'validationMethod' :  './validation/collector.sh',
                   u'qualificationMethod' : './validation/collector.sh',
                   u'startMethod' : '',
                   u'stopMethod' : ''
                   },
    u'perfdata'    : { 
                   u'priority' : -1,
                   u'validationMethod' :  './validation/perfdata.sh',
                   u'qualificationMethod' : './validation/perfdata.sh',
                   u'startMethod' : '',
                   u'stopMethod' : ''
                   },
    u'supnav'    : { 
                   u'priority' : -1,
                   u'validationMethod' :  './validation/supnav.sh',
                   u'qualificationMethod' : './validation/supnav.sh',
                   u'startMethod' : '',
                   u'stopMethod' : ''
                   },
    u'nagvis'    : { 
                   u'priority' : -1,
                   u'validationMethod' :  './validation/nagvis.sh',
                   u'qualificationMethod' : './validation/nagvis.sh',
                   u'startMethod' : '',
                   u'stopMethod' : ''
                   },
    u'rrdgraph'    : { 
                   u'priority' : -1,
                   u'validationMethod' :  './validation/rrdgraph.sh',
                   u'qualificationMethod' : './validation/rrdgraph.sh',
                   u'startMethod' : '/etc/init.d/httpd reload',
                   u'stopMethod' : ''
                   },
    u'reportingv2' : {
                   u'priority' : -1,
                   u'validationMethod' :  '',
                   u'qualificationMethod' : '',
                   u'startMethod' : '',
                   u'stopMethod' : ''
                   },
}


appsByAppGroups = {
    u'collect'           : [u'nagios', u'collector', u'perfdata'],
    u'metrology'         : [u'connector-metro', u'rrdgraph'],
    u'corrpres'          : [u'supnav', u'apacheRP', u'nagvis'],
    u'reporting'         : [u'reportingv2'],
    u'trap'              : [u'corrtrap'],
}


confid = "$Rev$"[6:-2]

# vim:set expandtab tabstop=4 shiftwidth=4:
