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
        test_plugin,
        eventFilter,
        args,
    )
    reg.logger.debug("Registered callback.")


def is_valid(sg, logger, args):
    """
    Validate our args.

    :param sg: Shotgun API handle.
    :param logger: Logger instance.
    :param args: Any additional misc arguments passed through this plugin.
    :returns: True if plugin is valid, None if not.
    """

    # Make sure args["entity_status_field"] is still in our entity schema.
    try:
        entity_schema = sg.schema_field_read(
            args["entity_type"],
            field_name=args["entity_status_field"],
        )
    except Exception, e:
        logger.warning(
            "%s does not exist in %s schema, skipping: %s" % (
                args["entity_status_field"],
                args["entity_type"],
                e.message,
            )
        )
        return

    # Make sure args["target_status"] is in the entity schema.
    if args["target_status"] not in entity_schema["sg_status_list"]["properties"]["valid_values"]["value"]:
        logger.warning(
            "%s is not in %s schema, plugin will never execute." % (
                args["target_status"],
                args["entity_type"],
            )
        )
        return

    # Make sure the Task schema has an args["target_status"] field.
    task_schema = sg.schema_field_read(
        "Task",
        field_name="sg_status_list",
    )
    if args["target_status"] not in task_schema["sg_status_list"]["properties"]["valid_values"]["value"]:
        logger.warning("%s is not in Task schema, plugin will never execute." % args["task_status"])
        return

    return True


def test_plugin(sg, logger, event, args):
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

