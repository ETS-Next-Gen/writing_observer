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
def fetch_doc_at_timestamp(overall_timestamps, requested_timestamp=None):
    '''
    Iterate over a list of students and determine their latest document
    in reference to the `requested_timestamp`.

    `requested_timestamp` should be a string of ms since unix epoch
    '''
    output = []
    for student in overall_timestamps:
        timestamps = student.get('timestamps', {})
        student['doc_id'] = ''
        if requested_timestamp is None:
            # perhpas this should fetch the latest doc id instead
            output.append(student)
            continue
        sorted_ts = sorted(timestamps.keys())
        bisect_index = bisect.bisect_right(sorted_ts, requested_timestamp) - 1
        if bisect_index < 0:
            output.append(student)
            continue
        target_ts = sorted_ts[bisect_index]
        student['doc_id'] = timestamps[target_ts]
        output.append(student)
    return output
