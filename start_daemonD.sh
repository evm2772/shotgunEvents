#!/usr/bin/env bash

export PYTHONPATH=${PYTHONPATH}:/mnt/storage/rnd_tools/ppline/dev/python-api


export SG_SERVER='https://filmdirectionfx.shotgunstudio.com'

#test plugin:
export SGDAEMON_SCRIPT_NAME=shotgunEventDaemon
export SGDAEMON_SCRIPT_KEY='hcjbtwtfv$n0foiQqdfrlaemg'


python2 /mnt/storage/rnd_tools/ppline/dev/shotgunEvents/src/shotgunEventDaemon.py foreground