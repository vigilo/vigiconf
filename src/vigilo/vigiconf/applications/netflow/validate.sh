#!/bin/sh                                                                                                                                    
if [ "$2" == "local" ] ; then
    ls /etc/init.d/nfacctd >/dev/null || exit 1
fi
exit 0
