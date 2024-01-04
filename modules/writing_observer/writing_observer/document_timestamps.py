import bisect

import learning_observer.communication_protocol.integration


@learning_observer.communication_protocol.integration.publish_function('source_selector')
def select_source(sources, source):
    '''
    Given a variety of sources, pick which source we should use.

    HACK With this as a function, the system will run every node
    available in `sources`. If we created this as a dispatch type
    within the protocol, we could make it so the system only runs
    the requested source node.
    TODO make this a dispatch type within the protocol
    '''
    if source not in sources:
        raise KeyError(f'Source, `{source}`, not found in available sources: {sources.keys()}')
    return sources[source]


@learning_observer.communication_protocol.integration.publish_function('writing_observer.fetch_doc_at_timestamp')
def fetch_doc_at_timestamp(timestamps, requested_timestamp=None):
    '''
    Given a dictionary of timestamps (keys) and doc_ids (values),
    fetch the doc_id closest to the requested timestamp without
    going over.
    '''
    if requested_timestamp is None:
        # perhpas this should fetch the latest doc id instead
        return {'doc_id': ''}
    sorted_ts = sorted(timestamps.keys())
    bisect_index = bisect.bisect_right(sorted_ts, requested_timestamp) - 1
    if bisect_index < 0:
        return None
    target_ts = sorted_ts[bisect_index]
    return {'doc_id': timestamps[target_ts][0]}
