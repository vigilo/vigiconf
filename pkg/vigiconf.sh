#!/bin/bash

dir=@DATADIR@

if [ "`whoami`" != "vigiconf" ]; then
	echo "I must be run by the 'vigiconf' user !"
	exit 1
fi

function usage() {
	echo "Usage: vigiconf <generator|validator|dispatchator|conf|ventilator>"
	exit 2
}

if [ -n "$1" -a -f $dir/$1.py ]; then
	command=$1
	shift
elif [ "$1" == "--help" -o "$1" == "-h" ]; then
	usage
else
	command="dispatchator"
fi

# We need at least python 2.5
python=python
which python2.5 >/dev/null 2>&1
if [ $? = 0 ]; then
    python=python2.5
else
    pyver=`python -V 2>&1 | cut -d' ' -f2 | tr -d .`
    if [ $pyver -lt "250" ]; then
        echo "We need at least python 2.5 to work. Aborting."
        exit 1
    fi
fi

cd $dir
exec $python ./$command.py $@
