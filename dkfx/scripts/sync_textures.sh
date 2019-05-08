#!/usr/bin/env bash

export MAYA_MODULE_PATH="/opt/solidangle/mtoa/2018"
export MAYA_DISABLE_CIP=1
export PYTHONPATH=${PYTHONPATH}:/mnt/storage/rnd_tools/ppline/prod/tools
#export MAYA_APP_DIR="/home/emelkov/devel/maya_prefs/maya/2018/prefs"
export solidangle_LICENSE=5053@localhost

export STORAGE_TEXTURES_DIR=$1
export PANASAS_TEXTURES_DIR=$2
export PROJECT_ID=$3


echo "STORAGE_TEXTURES_DIR = ${STORAGE_TEXTURES_DIR}"
echo "PANASAS_TEXTURES_DIR = ${PANASAS_TEXTURES_DIR}"
echo "PROJECT_ID = ${PROJECT_ID}"
/usr/autodesk/maya/bin/mayapy /mnt/storage/rnd_tools/ppline/prod/shotgunEvents/dkfx/scripts/export_tx.py "$@"


