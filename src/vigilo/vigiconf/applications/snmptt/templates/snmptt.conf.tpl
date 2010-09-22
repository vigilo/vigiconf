EVENT %(event)s %(oid)s "Status Events" Normal
FORMAT Receive $*
EXEC "%(command)s" "%(host)s" "%(service)s" $*
%(match)s
SDESC
EDESC

