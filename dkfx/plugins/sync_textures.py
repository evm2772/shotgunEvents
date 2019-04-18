# -*- coding: utf-8 -*-
# Copyright 2018 Autodesk, Inc.  All rights reserved.
#
# Use of this software is subject to the terms of the Autodesk license agreement
# provided at the time of installation or download, or which otherwise accompanies
# this software in either electronic or hard copy form.
#

# See docs folder for detailed usage info.

import os
import logging


def registerCallbacks(reg):
    """
    Register all necessary or appropriate callbacks for this plugin.
    """

    # Specify who should recieve email notifications when they are sent out.
    #
    # reg.setEmails('me@mydomain.com')

    # Use a preconfigured logging.Logger object to report info to a log file or
    # email. By default error and critical messages will be reported via email
    # and logged to file, all other levels are logged to a file.
    #
    # reg.logger.debug('Loading logArgs plugin.')

    # Register a callback to into the event processing system.
    #
    # Arguments:
    # - Shotgun script name
    # - Shotgun script key
    # - Callable
    # - A filter to match events to so the callable is only invoked when
    #   appropriate
    # - Argument to pass through to the callable
    #
    # eventFilter = {'Shotgun_Task_Change': ['sg_status_list']}

    eventFilter = {'Shotgun_Task_Change': 'sg_status_list'}

    reg.registerCallback(
        os.environ["SGDAEMON_LOGARGS_NAME"],
        os.environ["SGDAEMON_LOGARGS_KEY"],
        sync_textures,
        eventFilter,
        None,
    )


    # Set the logging level for this particular plugin. Let debug and above
    # messages through (don't block info, etc). This is particularly usefull
    # for enabling and disabling debugging on a per plugin basis.
    reg.logger.setLevel(logging.DEBUG)

from pprint import pprint, pformat
import subprocess
import traceback
import fnmatch
import re

def textures_parser(root_folder, logger):
    masks = ["*.bmp", "*.exr", "*.gif", "*.hdri", "*.jpeg", "*.jpg", "*.png", "*.psd", "*.tiff", "*.tif", "*.tga"]
    includes = '|'.join([fnmatch.translate(x) for x in masks])
    #print includes
    texture_paths = []
    for (dirpath, dirnames, filenames) in os.walk(root_folder):
        if dirnames:
            # find versions:
            version_dirs = [d for d in dirnames if re.match(r'v\d\d', d)]
            if version_dirs:
                version_dirs.sort() # for any case ;-)
                last_version_dir = os.path.join(dirpath, version_dirs[-1])
                logger.debug('Last version dir: {0} --> {1}'.format(version_dirs, last_version_dir))
                for (dirpath, dirnames, filenames) in os.walk(last_version_dir):
                    files = [f for f in filenames if re.match(includes, f)]
                    logger.debug ('Found files: %s' % str(files))
                    for f in files:
                        texture_paths.append(os.path.join(last_version_dir, f))

    logger.debug('Files for sync: \n %s' % pformat(texture_paths))
    return texture_paths

    

def sync_textures(sg, logger, event, args):
    """
    A callback that logs its arguments.

    :param sg: Shotgun API handle.
    :param logger: Logger instance.
    :param event: A Shotgun EventLogEntry entity dictionary.
    :param args: Any additional misc arguments passed through this plugin.
    """
    logger.debug("Event: %s" % pformat(dict(event)))
    logger.debug("Entity: %s" % pformat(dict(event['entity'])))
    logger.debug("Meta: %s" % pformat(dict(event['meta'])))

    task_name = event['entity']['name']
    new_status = event['meta']['new_value']
    old_status = event['meta']['old_value']
    logger.debug("%s status: %s --> %s" % (event['entity'], old_status, new_status))
    # try:
    #     #task_entity = sg.find_one('Task', [['id', 'is', event['entity']['id']]], ['entity'])
    #     filters = [['tasks', 'is', event['entity']]]
    #     fields = ['code', 'sg_published_files']
    #     # найдем ассет или сабассет с этим таском
    #     task_entity = sg.find_one('CustomEntity01', filters, fields) or sg.find_one('Asset', filters, fields)
    #     #task_entity = sg.find_one('CustomEntity01', [[event['entity'], 'in', 'tasks']], [])
    #     logger.info(">>>> %s" % str(task_entity))
    #
    #
    #     filters = [['linked_entity_type', 'in', ['Asset', 'CustomEntity01']],
    #                ['entity', 'is', task_entity]]
    #
    #
    #     fields = ['path']
    #     # путь к ассету или сабассету
    #     filesys_loc = sg.find_one('FilesystemLocation', filters, fields)
    #     logger.info(">>>> filesys_loc = %s" % pformat(filesys_loc))
    # except Exception as err:
    #     print ('EXCEPTION!!!')
    #     logger.debug(traceback.format_exc())
    if task_name == 'texture' and new_status == 'cmpt':
        # найдем ассет или сабассет с этим таском
        # filters = [['tasks', 'is', event['entity']]]
        # fields = ['code']
        # task_entity = sg.find_one('CustomEntity01', filters, fields) or sg.find_one('Asset', filters, fields)
        # logger.debug('%s' % task_entity)



        logger.info("-----------  BINGO. Sync starts: %s" % task_name)

        # найдем ассет или сабассет с этим таском
        filters = [['tasks', 'is', event['entity']]]
        fields = ['code', 'sg_published_files']
        task_entity = sg.find_one('CustomEntity01', filters, fields) or sg.find_one('Asset', filters, fields)
        logger.debug("Asset or Subasset:  %s" % str(task_entity))

        # путь к ассету или сабассету
        filters = [['linked_entity_type', 'in', ['Asset', 'CustomEntity01']],
                   ['entity', 'is', task_entity]]
        fields = ['path']
        filesys_loc = sg.find_one('FilesystemLocation', filters, fields)

        filesys_locs = sg.find('FilesystemLocation', filters, fields)

        if len(filesys_locs) > 1:
            logger.error('Not single location: %s. Must be clean up')
            return

        if filesys_loc:
            #/mnt/storage/

            # Path to destination (Panasas):
            local_path_linux = filesys_loc['path']['local_path_linux']
            if not os.path.join(local_path_linux.startswith('/fd/projects/')):
                logger.error ('Incorrect location: %s. Must be on "Panasas!"' % os.path.join(local_path_linux))
                return

            panasas_as_dir = os.path.join(filesys_loc['path']['local_path_linux']) # on panasas!!!
            panasas_textures_dir = os.path.join(panasas_as_dir, 'textures')  # on panasas!!!
            logger.debug('"Panasas" textures directory: %s' % panasas_textures_dir)
            if not os.path.isdir(panasas_textures_dir):
                logger.debug('"Panasas" textures directory is not found. Creating: %s' % panasas_textures_dir)
                os.makedirs(panasas_textures_dir) #todo return
                logger.debug('"Panasas" textures directory was created:  %s' % panasas_textures_dir)


            # Path to source (Storage!)
            storage_as_dir = panasas_as_dir.replace('/fd/projects/', '/mnt/storage/') # on storage!!!

            if not os.path.isdir(storage_as_dir):
                logger.error('"Storage" asset(subasset) directory is not found: %s' % storage_as_dir)
                # todo note?
                return

            storage_textures_dir = os.path.join(storage_as_dir, 'textures')
            logger.debug('"Storage" textures directory: %s' % storage_textures_dir)
            if not os.path.isdir(storage_textures_dir):
                logger.error('"Storage" textures directory not found: %s' % storage_textures_dir)
                # todo note?
                return
            
            files = textures_parser(storage_textures_dir, logger)
        else:
            logger.error('No filesystem location. Must be corrected.')
            return

        script = os.path.normpath(os.path.join(os.path.dirname(__file__), '../sh/sync_textures.sh'))
        logger.debug('script = %s' % script)

        for f in files:
            #dst_f = os.path.join(panasas_textures_dir, os.p ath.basename(f))

            #os.system('cp %s %s' % (f, dst_f))
            cmd = 'rsync -av --delete %s %s' % (f, panasas_textures_dir)
            proc = subprocess.Popen(cmd, shell=True)

            logger.debug('#### rsync: %s --> %s' % (f, panasas_textures_dir))
            #panasas_textures_dir
