'''
Common utility functions
'''
import functools

import kvs


def kvs_pipeline(streammodule):
    '''
    Closures, anyone?

    There's a bit to unpack here.

    Top-level function. This allows us to configure the decorator (and
    returns the decorator)
    '''
    def decorator(func):
        '''
        The decorator itself
        '''
        @functools.wraps(func)
        def wrapper_closure(metadata):
            '''
            The decorator itself. We create a function that, when called,
            creates an event processing pipeline. It keeps a pointer
            to the KVS inside of the closure. This way, each pipeline has
            its own KVS. This is the level at which we want consistency,
            want to allow sharding, etc. If two users are connected, each
            will have their own data store connection.
            '''
            print("Metadata: ")
            print(metadata)
            if metadata is not None and 'auth' in metadata:
                safe_user_id = metadata['auth']['safe_user_id']
            else:
                safe_user_id = '[guest]'
                # TODO: raise an exception.

            keynamespace = "{streammodule}:{user}".format(
                streammodule=streammodule,
                user=safe_user_id
            )
            taskkvs = kvs.KVS()

            async def process_event(events):
                '''
                This is the function which processes events. It calls the event
                processor, passes in the event(s) and state. It takes
                the internal state and the external state from the
                event processor. The internal state goes into the KVS
                for use in the next call, while the external state
                returns to the dashboard.

                The external state should include everything needed
                for the dashboard visualization and exclude anything
                large or private. The internal state needs everything
                needed to continue reducing the events.
                '''
                internal_state = await taskkvs[keynamespace]
                internal_state, external_state = await func(
                    events, internal_state
                )
                await taskkvs.set(keynamespace, internal_state)
                return external_state
            return process_event
        return wrapper_closure
    return decorator
