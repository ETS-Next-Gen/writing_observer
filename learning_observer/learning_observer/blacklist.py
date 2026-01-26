import pmss

import learning_observer.settings
import learning_observer.util

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

# Register blacklist settings
pmss.parser('blacklist_event_action', parent='string', choices=action_modes, transform=None)
pmss.register_field(
    name='blacklist_event_action',
    type='blacklist_event_action',
    description='How to treat incoming events for blacklist checks.',
    default=ACTIONS.TRANSMIT
)
pmss.parser('blacklist_time_limit', parent='string', choices=time_limits, transform=None)
pmss.register_field(
    name='blacklist_time_limit',
    type='blacklist_time_limit',
    description='Time limits for MAINTAIN/PERMANENT blacklist responses.',
    default=TIME_LIMITS.MINUTES
)


def _extract_event_domain(event):
    '''Find the domain of a user via the event
    HACK we do not include the user's email throughout the incoming
    event pipeline. We might do that in the future. For now, we look
    in the places where an email *might* be to extract the domain.
    '''
    if not isinstance(event, dict):
        return None
    email = None
    if 'chrome_identity' in event:
        email = event['chrome_identity'].get('email')
    return learning_observer.util.get_domain_from_email(email)


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
    event_domain = _extract_event_domain(event)
    attributes = {'domain': event_domain} if event_domain else {}
    action_type = learning_observer.settings.pmss_settings.blacklist_event_action(types=['incoming_events'], attributes=attributes)

    if action_type == ACTIONS.MAINTAIN:
        # tell client to keep messages around
        time_limit = learning_observer.settings.pmss_settings.blacklist_time_limit(
            types=['incoming_events'],
            attributes=attributes
        )
        return {
            'status': 'blocklist',
            'action': ACTIONS.MAINTAIN,
            'time_limit': time_limit,
            'message': 'You are blocked for now'
        }
    if action_type == ACTIONS.DROP:
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
