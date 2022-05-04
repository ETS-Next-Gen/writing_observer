'''
Learning Observer Library

Helpers to support the use of Learning Observer in scripts, in
other applications, and in Jupyter notebooks.
'''
import argparse
import asyncio
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
            "debug-log-level": "NONE",
            "debug-log-destination": ["console"]
        },
        "kvs": {
            "type": "stub",
        },
        "config": {
            "run_mode": "dev"
        }
    })

    # Initialize the system
    learning_observer.log_event.DEBUG_LOG_LEVEL = learning_observer.log_event.LogLevel.NONE
    reducers = learning_observer.module_loader.reducers()
    learning_observer.kvs.kvs_startup_check()
    learning_observer.stream_analytics.init()


async def process_file(file_path, source=None, userid=None):
    '''
    Process a single log file.

    Args:
        file_path (str): The path to the log file to process.
        source (str): The source of events (e.g. org.mitros.dynamic-assessment)
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

    n = 0 # Number of events processed
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


async def process_dir(path = os.getcwd()):
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
    '''
    kvs = learning_observer.kvs.KVS()
    await kvs.clear()
