#!/bin/sh

python /usr/lib/python2.3/profile.py pydance.py > /dev/null
mv ~/.pydance/pydance.log Profile-`date +%s`
