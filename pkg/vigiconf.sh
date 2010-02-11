#!/bin/bash

if [ "`whoami`" = "root" ]; then
	# Re-exec myself as the vigiconf user
	exec su - vigiconf -c "$0 $@"
fi

if [ "`whoami`" != "vigiconf" ]; then
	echo "I must be run by the 'vigiconf' user !"
	exit 1
fi

dispatchator=`which vigiconf-dispatchator 2>/dev/null`
if [ ! -e "$dispatchator" ]; then
	dispatchator=`dirname $0`/vigiconf-dispatchator
	if [ ! -e "$dispatchator" ]; then
		echo "Can't find vigiconf-dispatchator. Make sure it's in the PATH"
		exit 1
	fi
fi

exec $dispatchator -r -d -f $@
