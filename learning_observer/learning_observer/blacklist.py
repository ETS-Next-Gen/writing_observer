# TODO:
# ACTIONS = enum.StrEnum("ACTIONS", names=('TRANSMIT', 'MAINTAIN', 'DROP'))
#
# I believe the above requires Python 3.11 or newer.

# TODO These values ought to live in a shared space to be
# imported by both this code and lo_event.
class ACTIONS:
    pass
action_modes = ['TRANSMIT', 'MAINTAIN', 'DROP']
[setattr(ACTIONS, action, action) for action in action_modes]

class TIME_LIMITS:
    pass
time_limits = ['PERMANENT', 'MINUTES', 'DAYS']
[setattr(TIME_LIMITS, limit, limit) for limit in time_limits]


def get_blacklist_status(event):
    '''Return the blacklist status of a given event
    Returns should look like:
    `{ 
        status: 'blocklist',
        action,
        time_limit,
        message
    }`
    '''
    # TODO add in the logic to check our blacklist
    if False:
        # tell client to keep messages around
        return {
            'status': 'blocklist',
            'action': ACTIONS.MAINTAIN,
            'time_limit': TIME_LIMITS.MINUTES,  # Note this could (and usually would) be a number, but we have a few defaults like 'MINUTES' defined
            'message': 'You are blocked for now'
        }
    if False:
        # tell client to drop messages
        return {
            'status': 'blocklist',
            'action': ACTIONS.DROP,
            'time_limit': TIME_LIMITS.PERMANENT,
            'message': 'Do not send more messages to me'
        }
    # transmit messages
    return {
        'status': 'blocklist',
        'action': ACTIONS.TRANSMIT,
    }
