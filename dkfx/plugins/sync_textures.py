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
    try:
        #task_entity = sg.find_one('Task', [['id', 'is', event['entity']['id']]], ['entity'])
        filters = [['tasks', 'is', event['entity']]]
        fields = ['code', 'sg_published_files']
        # найдем ассет или сабассет с этим таском
        task_entity = sg.find_one('CustomEntity01', filters, fields) or sg.find_one('Asset', filters, fields)
        #task_entity = sg.find_one('CustomEntity01', [[event['entity'], 'in', 'tasks']], [])
        logger.info(">>>> %s" % str(task_entity))


        filters = [['linked_entity_type', 'in', ['Asset', 'CustomEntity01']],
                   ['entity', 'is', task_entity]]

        
        fields = ['path']
        filesys_loc = sg.find_one('FilesystemLocation', filters, fields)
        logger.info(">>>> filesys_loc = %s" % pformat(filesys_loc))
    except Exception as err:
        print ('EXCEPTION!!!')
        logger.debug(traceback.format_exc())
    if task_name == 'texture' and new_status == 'cmpt':
        logger.info("BINGO. Sync starts: %s" % task_name)
        script = os.path.normpath(os.path.join(os.path.dirname(__file__), '../sh/sync_textures.sh'))
        logger.debug('script = %s' % script)
        #task_entity = sg.find_one('Task', [['id', 'is', event['entity']['id']]], ['entity']) #



        # got like this : {'type': 'Task', 'id': 31207, 'entity': {'type': 'CustomEntity01', 'id': 93, 'name': 'basement'}}

    #subprocess.call('')
