# -*- coding: utf-8 -*-
# Copyright 2018 Autodesk, Inc.  All rights reserved.
#
# Use of this software is subject to the terms of the Autodesk license agreement
# provided at the time of installation or download, or which otherwise accompanies
# this software in either electronic or hard copy form.
#

# See docs folder for detailed usage info.

import os
import sys
import logging
from pprint import pprint, pformat
import subprocess
import traceback
import fnmatch
import re


# def textures_parser(root_folder, logger):
#     masks = ["*.bmp", "*.exr", "*.gif", "*.hdri", "*.jpeg", "*.jpg", "*.png", "*.psd", "*.tiff", "*.tif", "*.tga"]
#     includes = '|'.join([fnmatch.translate(x) for x in masks])
#     texture_paths = []
#     for (dirpath, dirnames, filenames) in os.walk(root_folder):
#         if dirnames:
#             # find versions:
#             version_dirs = [d for d in dirnames if re.match(r'v\d\d', d)]
#             if version_dirs:
#                 version_dirs.sort() # for any case ;-)
#                 last_version_dir = os.path.join(dirpath, version_dirs[-1])
#                 logger.debug('Last version dir: {0} --> {1}'.format(version_dirs, last_version_dir))
#                 for (dirpath, dirnames, filenames) in os.walk(last_version_dir):
#                     files = [f for f in filenames if re.match(includes, f)]
#                     logger.debug ('Found files: %s' % str(files))
#                     for f in files:
#                         texture_paths.append(os.path.join(last_version_dir, f))
#
#     logger.debug('Files for sync: \n %s' % pformat(texture_paths))
#     return texture_paths

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
        os.environ["SGDAEMON_SCRIPT_NAME"],
        os.environ["SGDAEMON_SCRIPT_KEY"],
        sync_textures,
        eventFilter,
        None,
    )


    # Set the logging level for this particular plugin. Let debug and above
    # messages through (don't block info, etc). This is particularly usefull
    # for enabling and disabling debugging on a per plugin basis.
    reg.logger.setLevel(logging.DEBUG)


def sync_textures(sg, logger, event, args):
    """
    A callback that logs its arguments.

    :param sg: Shotgun API handle.
    :param logger: Logger instance.
    :param event: A Shotgun EventLogEntry entity dictionary.
    :param args: Any additional misc arguments passed through this plugin.

    event ex.: {'attribute_name': 'sg_status_list',
             'created_at': datetime.datetime(2019, 5, 16, 12, 7, 12, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7fa4aef43910>),
             'entity': {'id': 29343, 'name': 'txtr', 'type': 'Task'},
             'event_type': 'Shotgun_Task_Change',
             'id': 2949503,
             'meta': {'attribute_name': 'sg_status_list',
                      'entity_id': 29343,
                      'entity_type': 'Task',
                      'field_data_type': 'status_list',
                      'new_value': 'cmpt',
                      'old_value': 'hld',
                      'type': 'attribute_change'},
             'project': {'id': 92, 'name': 'SOUZ_S', 'type': 'Project'},
             'session_uuid': 'd4e4e4b0-7730-11e9-90b5-0242ac110004',
             'type': 'EventLogEntry',
             'user': {'id': 198, 'name': 'Evgeniy Melkov', 'type': 'HumanUser'}
             }

    """




    #
    # field_name = event.get("attribute_name")
    # entity = event.get("entity")
    # project = event.get("project")
    # new_value = event.get("meta", {}).get("new_value")
    # old_value = event.get("meta", {}).get("new_value")
    # user = event.get("user")
    # event_id = event.get("id")


    entity = event.get("entity")
    project = event.get("project")
    user = event.get("user")
    meta = event.get("meta")

    # Make sure all our event keys contain values.
    if None in [entity, project, user, meta]:
        logger.warning("Missing info in event dictionary, skipping.")
        return


    # if user['id'] != 198:
    #     logger.warning('################################# Not developer user. Skipping')
    #     return
    # else:
    #     logger.warning('BINGO! DEVELOPER EVM ... ')


    task_name = entity.get('name')
    new_status = meta.get('new_value')
    old_status = meta.get('old_value')
    project_id = project.get('id')  # {'id': 92, 'name': 'SOUZ_S', 'type': 'Project'}

    logger.debug("%s status: %s --> %s" % (event['entity'], old_status, new_status))

    if task_name == 'txtr' and new_status == 'cmpt':
        logger.debug('event: %s' % pformat(event))
        # найдем ассет или сабассет с этим таском
        # filters = [['tasks', 'is', event['entity']]]
        # fields = ['code']
        # task_entity = sg.find_one('CustomEntity01', filters, fields) or sg.find_one('Asset', filters, fields)
        # logger.debug('%s' % task_entity)
        logger.info("Copy textures to Panasas starts: %s" % task_name)

        # найдем ассет или сабассет с этим таском
        filters = [['tasks', 'is', event['entity']]]
        fields = ['code', 'sg_published_files']
        task_entity = sg.find_one('CustomEntity01', filters, fields) or sg.find_one('Asset', filters, fields)
        logger.debug("Asset or Subasset:  %s" % str(task_entity))

        # путь к ассету или сабассету
        filters = [['linked_entity_type', 'in', ['Asset', 'CustomEntity01']],
                   ['entity', 'is', task_entity]]
        fields = ['path']
        #filesys_loc = sg.find_one('FilesystemLocation', filters, fields)
        filesys_locs = sg.find('FilesystemLocation', filters, fields)
        
        if not filesys_locs:
            logger.warning('No one location found. Skipped.')
            return

        if len(filesys_locs) > 1:
            logger.warning('Not single location: %s. Must be clean up')
            return

        filesys_loc = filesys_locs[0]
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
                os.makedirs(panasas_textures_dir)
                logger.debug('"Panasas" textures directory was created:  %s' % panasas_textures_dir)


            # Path to source (Storage!)
            storage_as_dir = panasas_as_dir.replace('/fd/projects/', '/mnt/storage/') # on storage!!!

            if not os.path.isdir(storage_as_dir):
                logger.error('"Storage" asset(subasset) directory is not found: %s' % storage_as_dir)
                return

            storage_textures_dir = os.path.join(storage_as_dir, 'textures')
            logger.debug('"Storage" textures directory: %s' % storage_textures_dir)
            if not os.path.isdir(storage_textures_dir):
                logger.error('"Storage" textures directory not found: %s' % storage_textures_dir)
                return
            
            #files = textures_parser(storage_textures_dir, logger)
        else:
            logger.error('No filesystem location. Must be corrected.')
            return

        dst_log = os.path.join(panasas_textures_dir, 'auto_export.log')
        # cmd = os.path.normpath(os.path.join(os.path.dirname(__file__), '../scripts/sync_textures.sh %s %s %s > %s' %
        #                                     (storage_textures_dir, panasas_textures_dir, project_id, dst_log)))

        # debug:
        cmd = os.path.normpath(os.path.join(os.path.dirname(__file__), '../scripts/sync_textures.sh %s %s %s 2>&1 | tee %s' %
                                            (storage_textures_dir, panasas_textures_dir, project_id, dst_log)))
        
        subprocess.Popen(cmd, shell=True)




