'''
Learning Observer Library

Helpers to support the use of Learning Observer in scripts, in
other applications, and in Jupyter notebooks.
'''
import argparse
import asyncio
from cgi import print_arguments
import json
import sys
import os

import names

import learning_observer.settings
import learning_observer.stream_analytics
import learning_observer.module_loader
import learning_observer.incoming_student_event
import learning_observer.log_event
import learning_observer.kvs
import learning_observer.rosters
import learning_observer.dashboard


async def init():
    '''
    Initialize the Learning Observer library.

    Returns:
        None

    This function will load the settings, and initialize the KVS to
    run from memory.
    '''
    # Run from memory
    learning_observer.settings.load_settings({
        "logging": {
            "debug_log_level": "NONE",
            "debug_log_destination": ["console"]
        },
        "kvs": {
            "type": "stub",
        },
        "config": {
            "run_mode": "dev"
        },
        "roster_data": {
            "source": "all"
        }
    })

    # Initialize the system
    learning_observer.log_event.DEBUG_LOG_LEVEL = learning_observer.log_event.LogLevel.NONE
    reducers = learning_observer.module_loader.reducers()
    learning_observer.kvs.kvs_startup_check()
    learning_observer.stream_analytics.init()
    learning_observer.rosters.init()


async def process_file(file_path, source=None, userid=None):
    '''
    Process a single log file.

    Args:
        file_path (str): The path to the log file to process.
        source (str): The source of events (e.g. org.mitros.dynamic_assessment)
                      If not specified, the source will be inferred from the
                      events.
        userid (str): The userid of the user that generated the events. If not
                        specified, the userid will be generated with `names`.

    Returns:
        Number of events processed, source, and userid

    If `source` is not specified, the source will be inferred from the
    log file.

    If `userid` is not specified, a username will be generated with
    `names.get_first_name()`. We do this because we don't want to
    accidentally use a real name. This minimizes the risk of exposing
    PII. It'd be easy to infer the real name from the log file, but
    that should be done with care, and a parameter would be needed to
    enable this.
    '''
    if file_path.endswith('.log'):
        opener = open
    elif file_path.endswith('.log.gz'):
        opener = gzip.open
    else:
        raise ValueError("Unknown file type: " + file_path)

    if source is None:
        with opener(file_path, 'r') as fp:
            first_line = json.loads(fp.readline())
            source = first_line['client']['source']

    if userid is None:
        userid = names.get_first_name()

    pipeline = await learning_observer.incoming_student_event.student_event_pipeline({
        "source": source,
        "auth": {
            "user_id": userid,
            "safe_user_id": userid
        }
    })

    n = 0  # Number of events processed
    with opener(file_path) as fp:
        for line in fp.readlines():
            try:
                await pipeline(json.loads(line))
                n += 1
            except:
                print(line)
                raise

    return n, source, userid


async def process_files(files):
    '''
    Process a list of log files.

    Args:
        files (list): A list of log files to process.

    Returns:
        Total number of events processed

    This function will process each file in the list, and print the
    results.
    '''
    total = 0
    for file in files:
        n, source, userid = await process_file(file)
        print("{} events processed from {} with user ID {}".format(n, source, userid))
        total += n

    return total


async def process_dir(path=os.getcwd()):
    '''
    Process all log files in a directory.

    Args:
        path (str): The path to the directory to process.

    Returns:
        Number of files processed, total number of events processed

    This function will process all log files in the directory, and
    print the results.
    '''
    files = [os.path.join(path, f) for f in os.listdir(path) if f.endswith('.log')]
    events_processed = await process_files(files)
    return len(files), events_processed


async def reset():
    '''
    Reset the Learning Observer library, clearing all processed events
    from the KVS.

    In the future, this will also clear the modules, etc.
    '''
    kvs = learning_observer.kvs.KVS()
    await kvs.clear()


async def aggregate(module_id):
    '''
    Aggregate the results of a module.

    This has a lot of overlap with dashboard.py, and should be refactored.
    '''
    course_id = 12345
    course_aggregator_module, default_data = learning_observer.dashboard.find_course_aggregator(module_id)

    if course_aggregator_module is None:
        print("Bad module: ", module_id)
        available = learning_observer.module_loader.course_aggregators()
        print("Available modules: ", [available[key]['short_id'] for key in available])
        raise ValueError(text="Invalid module: {}".format(module_id))

    roster = await learning_observer.rosters.courseroster("request", course_id)
    student_state_fetcher = learning_observer.dashboard.fetch_student_state(
        course_id,
        module_id,
        course_aggregator_module,
        roster,
        default_data
    )
    aggregator = course_aggregator_module.get('aggregator', lambda x: {})
    sd = await student_state_fetcher()
    data = {
        "student_data": sd   # Per-student list
    }
    data.update(aggregator(sd))
    return data
