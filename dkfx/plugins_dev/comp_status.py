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
        "tasks": ['light'],  # trigger tasks
        "entity_status_field": "sg_status_list",
        "entity_type": "Task",
        "linked_entities": ["Shot"],
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
        comp_status,
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



def comp_status(sg, logger, event, args):
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
    old_value = event.get("meta", {}).get("old_value")
    user = event.get("user")
    event_id = event.get("id")

    logger.debug('new value: %s old value: %s' % (old_value, new_value))

    if os.environ.get("SG_EVENT_DAEMON_DEVELOP_MODE"):
        if user['id'] != 198:
            logger.warning('DEVMODE: -------------Not developer user. Skipping ------------')
            return
        else:
            logger.warning('DEVMODE: -------------Dev user welcome! ---------------')

    logger.debug('entity: %s' % pformat(event))
    # Make sure all our event keys contain values.
    if None in [event_id, field_name, entity, project, old_value, new_value, user]:
        logger.warning("Missing info in event dictionary, skipping.")
        return


    if entity['name'] not in args['tasks']:
        logger.warning("We are not interested in this task [%s], skipping." % entity['name'])
        return

    # Make sure the event exists in Shotgun.
    sg_event = sg.find_one(
        "EventLogEntry",
        [["id", "is", event_id]],
        ["description"],
    )
    if not sg_event:
        logger.warning("Could not find event with id %s, skipping." % event_id)
        return

    # Spit out a nice little note for the logger.
    logger.info("Running this plugin because %s." % sg_event["description"])

    # Re-query our entity for updated field values.
    entity = sg.find_one(
        entity["type"],
        [["id", "is", entity["id"]]],
        [field_name, "description"],
    )

    # Bail if our entity doesn't exist.
    if not entity:
        logger.warning(
            "%s with id %s does not exist, skipping." % (
                entity["type"],
                entity["id"],
            )
        )
        return

    # Bail if our entity's field value has changed (is not new_value).
    if not entity[field_name] == new_value:
        logger.warning(
            "%s with id %s's %s has changed from %s since event inception." % (
                entity["type"],
                entity["id"],
                field_name,
                new_value,
            )
        )
        return

    logger.debug('event: %s' % pformat(event))

    # Init a list for an sg.batch command, and a list for collecting messages.
    batch_data = []
    update_message = []

    filters = [['tasks', 'is', event['entity']]]
    fields = ['sg_status_list']

    entity = None
    for et in args['linked_entities']:
        entity = sg.find_one(et, filters, fields)
        if entity:
            logger.debug('For entity type %s found: %s' % (et, entity))
            break

    if entity['sg_status_list'] == 'cmpt':
        logger.debug('For entity %s status "Complete". Skipping daemon work."' % (entity))
        return

    # Find all tasks with complete geo and txtr
    tasks = sg.find(
        "Task",
        [
            ["entity", "is", entity],
            ["content", "in", ["comp", "light"]]
         ],
        ["sg_status_list", "content"],
    )

    # must contain 1 task:
    logger.debug('For entity type %s found: %s' % (et, tasks))
    tasks_statuses = {}
    for task in tasks:
        tasks_statuses[task['content']] = task['sg_status_list']
    logger.debug('All tasks found: %s' % pformat(tasks))

    if len(tasks_statuses.keys()) != 2:
        logger.warning('Must be "comp", "light"')
        return
    logger.debug('Task statuses %s' % pformat(tasks_statuses))
    # Ex: Task statuses = {'geo': 'cmpt', 'shad': 'wtg', 'txtr': 'cmpt'}
    # wtg, rdy
    comp_st = tasks_statuses['comp']
    light_st = tasks_statuses['light']

    logger.debug('comp_st = %s' % comp_st)
    logger.debug('light_st  = %s' % light_st)

    new_comp_st = None
    if light_st == 'cmpt' and (comp_st in ['wtg']):
        logger.debug('Trigger status chanched: %s --> %s' % (old_value, new_value))
        new_comp_st = 'rdy'

    if light_st in ['cmpt'] and comp_st not in ['wtg']:
        logger.debug('Trigger status chanched: %s --> %s' % (old_value, new_value))
        new_comp_st = 'rrq'

    if not new_comp_st:
        logger.debug('Not triggered. Skipping')
        return

    logger.debug('new satus: %s' % (new_comp_st,))
    if comp_st == new_comp_st:
        logger.debug('New status [%s] she same as old. Skipping' % new_comp_st)
        return
    for task in tasks:
        # skip:
        if task['content'] in ['light']:
            continue
        if comp_st not in args["skip_statuses"]:
            update_message.append("Task with id %s" % task["id"])
            batch_data.append(
                {
                    "request_type": "update",
                    "entity_type": "Task",
                    "entity_id": task["id"],
                    "data": {"sg_status_list": new_comp_st},
                }
            )

    # Run the API batch command and tell the logger about it.
    logger.info(
        "Running batch API command to update the following: %s..." % ", ".join(update_message)
    )
    sg.batch(batch_data)
    logger.info("Done.")
