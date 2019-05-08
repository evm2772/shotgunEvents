#!/usr/bin/env bash

export PYTHONPATH=${PYTHONPATH}:/mnt/storage/rnd_tools/ppline/prod/python-api


export SG_SERVER='https://filmdirectionfx.shotgunstudio.com'

#test plugin:
export SGDAEMON_SCRIPT_NAME=shotgunEventDaemon
export SGDAEMON_SCRIPT_KEY='nlopr$ybdfik8ggulfqvxtFib'


python2 /mnt/storage/rnd_tools/ppline/prod/shotgunEvents/src/shotgunEventDaemon.py foreground