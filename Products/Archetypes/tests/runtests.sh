#!/bin/sh

export SOFTWARE_HOME="/usr/lib/zope/2.7-branch-23/lib/python"
export INSTANCE_HOME="/var/lib/zope/plone"

python2.3 runalltests.py
