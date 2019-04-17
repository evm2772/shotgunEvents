#!/usr/bin/env bash

export PYTHONPATH=${PYTHONPATH}:/mnt/storage/rnd_tools/ppline/dev/python-api

#test plugin:
export SGDAEMON_LOGARGS_NAME=sync_textures.py
export SGDAEMON_LOGARGS_KEY='cpzkhirtrtp)wrruljddfz7Rs'

python2 /mnt/storage/rnd_tools/ppline/dev/shotgunEvents/src/shotgunEventDaemon.py foreground