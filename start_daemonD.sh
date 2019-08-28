#!/usr/bin/env bash


export SG_EVENT_DAEMON_DEVELOP_MODE='ON'
echo '------------------develop mode --------------------'
export PYTHONPATH=${PYTHONPATH}:/fd/rnd_tools/ppline/dev/python-api


export SG_SERVER='https://filmdirectionfx.shotgunstudio.com'

#test plugin:
export SGDAEMON_SCRIPT_NAME=shotgunEventDaemonD
export SGDAEMON_SCRIPT_KEY='hcjbtwtfv$n0foiQqdfrlaemg'


python2 /fd/rnd_tools/ppline/dev/shotgunEvents/src/shotgunEventDaemon.py foreground