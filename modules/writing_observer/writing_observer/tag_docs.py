'''
These functions are used to get the appropriate behavior for
grouping tagged documents together. Lots of this code could
be transferred to a query commands in the execution protocol.
I tried to keep it generic enough so we could easily move
them later on, I just didn't want to do the added work of
creating new query commands.
'''
import copy

import learning_observer.util
import learning_observer.communication_protocol.integration


@learning_observer.communication_protocol.integration.publish_function('unwind')
def unwind(objects, value_path, new_name, keys_to_keep=None):
    '''
    Transforms each object with an array, `value_path`, into a series of separate
    objects, one for each object/unique `value_path` item pair.

    Objects can be a single object or a list of objects.

    :param keys_to_keep: List of keys to return. If `None`, all keys are returned except the head of `value_path`
    :default keys_to_keep: None
    :type keys_to_keep: list

    TODO this ought to be query command, I'm just writing it as a function for now
    but I'll try to keep it generic to be slid in later.
    '''
    items = [objects] if type(objects) != list else objects
    remove_key = value_path.split('.')[0]
    unpacked = []
    for item in items:
        # should we default or should we error? Probably error, maybe later
        values = learning_observer.util.get_nested_dict_value(item, value_path, [])
        for value in values:
            new = copy.deepcopy(item)
            # TODO handle proper removal of all keys except the `keys_to_keep`
            # Perhaps we need a function similar to that of get_nested_dict_value that removes them instead
            if remove_key in new:
                del new[remove_key]
            new[new_name] = value
            unpacked.append(new)
    return unpacked


@learning_observer.communication_protocol.integration.publish_function('group_by')
def group_by(items, value_path):
    '''
    After fetching all the text from each pair of student/doc id, we want
    to regroup them by student. Appending each document to a list in the
    process.

    Currently this function is hardcoded for the tagging documents workflow.
    Ideally we can determine which values we wish to keep as well as which
    functions to run on them.
    TODO abstract out of specific use case and implement as a query command
    '''
    overall = {}
    for item in items:
        import json
        print(json.dumps(item, indent=2))
        try:
            value = learning_observer.util.get_nested_dict_value(item, value_path)
        except KeyError:
            # TODO handle key not found
            continue
        if value in overall:
            overall[value]['documents'].append(item['text'])
        else:
            overall[value] = {}
            overall[value]['user_id'] = value
            overall[value]['documents'] = [item['text']]
    return [v for _, v in overall.items()]
