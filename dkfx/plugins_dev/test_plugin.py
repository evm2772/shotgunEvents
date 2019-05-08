# -*- coding: utf-8 -*-

import os
import shotgun_api3
from pprint import pprint, pformat

def registerCallbacks(reg):
    """
    This function is run when the Shotgun Event Daemon starts, if this file
    (__file__) lives in the plugin directory specified by the daemon's config
    file. Typically the registerCallback method should be called from the
    available reg object.

    :param object reg: A registrar object instance that can be used to register
                       a Callback function with the daemon.
    """


    # User-defined plugin args, change at will.
    args = {
        "target_status": "cmpt",
        "tasks": ['txtr', 'geo'],  # trigger tasks
        "entity_status_field": "sg_status_list",
        "entity_type": "Task",
        "linked_entities": ["Asset", "CustomEntity01"],
        "skip_statuses": []  #"fin", "na", "hld"],
    }

    # Grab authentication env vars for this plugin. Install these into the env
    # if they don't already exist.
    server = os.environ["SG_SERVER"]
    script_name = os.environ["SGDAEMON_SCRIPT_NAME"]
    script_key = os.environ["SGDAEMON_SCRIPT_KEY"]

    # Grab an sg connection for the validator.
    sg = shotgun_api3.Shotgun(server, script_name=script_name, api_key=script_key)

    # Bail if our validator fails.
    if not is_valid(sg, reg.logger, args):
        reg.logger.warning("Plugin is not valid, will not register callback.")
        return

    # We are only interested in changes to args["entity_type"] entities'
    # args["entity_status_field"] fields.
    eventFilter = {
        "Shotgun_%s_Change" % args["entity_type"]: args["entity_status_field"],
    }

    # Register our function with the dameon, and pass in our args.
    reg.registerCallback(
        script_name,
        script_key,
        shad_status,
        eventFilter,
        args,
    )
    reg.logger.debug("Registered callback.")


# EVENT: {'attribute_name': 'sg_status_list',
#  'created_at': datetime.datetime(2019, 4, 30, 15, 4, 45, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7f9d6a0bd8d0>),
#  'entity': {'id': 30495, 'name': 'ad', 'type': 'Task'},
#  'event_type': 'Shotgun_Task_Change',
#  'id': 2871499,
#  'meta': {'attribute_name': 'sg_status_list',
#           'entity_id': 30495,
#           'entity_type': 'Task',
#           'field_data_type': 'status_list',
#           'new_value': 'rdy',
#           'old_value': 'cmpt',
#           'type': 'attribute_change'},
#  'project': {'id': 92, 'name': 'SOUZ_S', 'type': 'Project'},
#  'session_uuid': '51cb3b12-6a9a-11e9-b201-0242ac110004',
#  'type': 'EventLogEntry',
#  'user': {'id': 198, 'name': 'Evgeniy Melkov', 'type': 'HumanUser'}}



def shad_status(sg, logger, event, args):
    """
    Смотрит на статус тасков geo и txtr. Если они complete - таску shad
    ставит статус rdy
    если один из них 'rrq' blb 'ip' - ставит hld

    :param object sg: An authenticated Shotgun Python API instance.
    :param object logger: A standard logger instance.
    :param dict event: Data related to a Shotgun EventLogEntry.
    :param dict args: Additional user-defined settings.
    :returns: None if the event can not be processed.
    """

    # Make some vars for convenience.
    field_name = event.get("attribute_name")
    entity = event.get("entity")
    project = event.get("project")
    new_value = event.get("meta", {}).get("new_value")
    old_value = event.get("meta", {}).get("new_value")
    user = event.get("user")
    event_id = event.get("id")
    

    logger.debug('event: %s' % pformat(event))
    # ------------------- rnd
    if user['id'] != 198:
        logger.warning('Not developer user. Skipping')
        return
    else:
        logger.warning('In develop. Starting .... ')
    # -----------------------

