'''
This is an interface to AWE_Workbench.
'''

import asyncio
import enum
import time
import functools
import os
import multiprocessing
import datetime
from collections import defaultdict
import json
import warnings

from concurrent.futures import ProcessPoolExecutor

import spacy
import coreferee
import spacytextblob.spacytextblob
import awe_components.components.lexicalFeatures
import awe_components.components.syntaxDiscourseFeats
import awe_components.components.viewpointFeatures
import awe_components.components.lexicalClusters
import awe_components.components.contentSegmentation


import writing_observer.nlp_indicators
import learning_observer.kvs
import learning_observer.util

RUN_MODES = enum.Enum('RUN_MODES', 'MULTIPROCESSING SERIAL')


def init_nlp():
    '''
    Initialize the spacy pipeline with the AWE components. This takes a while
    to run.
    '''
    warnings.filterwarnings('ignore', category=UserWarning, module='nltk')
    nlp = spacy.load("en_core_web_lg")

    # Adding all of the components, since
    # each of them turns out to be implicated in
    # the demo list. I note below which ones can
    # be loaded separately to support specific indicators.
    nlp.add_pipe('coreferee')
    nlp.add_pipe('spacytextblob')
    nlp.add_pipe('lexicalfeatures')
    nlp.add_pipe('syntaxdiscoursefeatures')
    nlp.add_pipe('viewpointfeatures')
    nlp.add_pipe('lexicalclusters')
    nlp.add_pipe('contentsegmentation')
    return nlp


nlp = init_nlp()


def outputIndicator(doc, indicatorName, itype, stype=None, text=None, added_filter=None):
    '''
    A function to output three types of information: summary metrics,
    lists of textual information selected by the indicator, and
    the offset information for each word or span selected by the indicator
    '''

    indicator = {}

    if added_filter is None:
        theFilter = [(indicatorName, [True]), ('is_alpha', [True])]
    else:
        theFilter = added_filter
        theFilter.append(('is_alpha', [True]))

    indicator['metric'] =\
        doc._.AWE_Info(infoType=itype,
                       indicator=indicatorName,
                       filters=theFilter,
                       summaryType=stype)

    data = json.loads(
        doc._.AWE_Info(infoType=itype,
                       indicator=indicatorName,
                       filters=theFilter)).values()

    indicator['offsets'] = \
        [[entry['offset'], entry['length']] for entry in data]

    if itype == 'Token':
        indicator['text'] = \
            json.loads(doc._.AWE_Info(infoType=itype,
                                      indicator=indicatorName,
                                      filters=theFilter,
                                      transformations=['lemma'],
                                      summaryType='uniq'))
    else:
        indicator['text'] = []

        for span in indicator['offsets']:
            indicator['text'].append(text[int(span[0]):int(span[0]) + int(span[1])])

    return indicator


def process_text(text, options=None):
    '''
    This will extract a dictionary of metadata using Paul's AWE Workbench code.
    '''
    doc = nlp(text)
    results = {}

    if options is None:
        # Do we want options to be everything initially or nothing?
        options = writing_observer.nlp_indicators.INDICATORS.keys()
        options = []

    for item in options:
        if item not in writing_observer.nlp_indicators.INDICATORS:
            continue
        indicator = writing_observer.nlp_indicators.INDICATORS[item]
        (id, label, infoType, select, filterInfo, summaryType) = indicator
        results[id] = outputIndicator(doc, select, infoType, stype=summaryType, text=text, added_filter=filterInfo)
        results[id].update({
            "label": label,
            "type": infoType,
            "name": id,
            "summary_type": summaryType
        })
    return results


async def process_texts_serial(texts, options=None):
    '''
    Process a list of texts, in serial.

    For testing / debugging, this will process a single essay. Note that while
    labeled async, it's not. If run on the server, it will lock up the main
    Python process.
    '''
    annotated = []
    for text in texts:
        print(text)
        annotations = process_text(text, options)
        annotations['text'] = text
        annotated.append(annotations)

    return annotated


executor = None


def run_in_fork(func):
    '''
    This will run a function in a forked subproces, for isolation.

    I wanted to check if this would solve a bug. It didn't.
    '''
    q = multiprocessing.Queue()
    thread = os.fork()
    if thread != 0:
        print("Awaiting queue")
        return q.get(block=True)
        print("Awaited")
    else:
        print("Queuing")
        q.put(func())
        print("Queued")
        os._exit(0)


async def process_texts_parallel(texts, options=None):
    '''
    This will spin up as many processes as we have cores, and process texts
    in parallel. Note that we should confirm issues of thread safety. If
    Python does this right, this should run in forked environments, and we
    won't run into issues. Otherwise, we'd want to either fork ourselves, or
    understand how well spacy, etc. do with parallelism.
    '''
    global executor
    if executor is None:
        executor = ProcessPoolExecutor()

    loop = asyncio.get_running_loop()
    result_futures = []
    for text in texts:
        processor = functools.partial(process_text, text, options)
        # forked_processor = functools.partial(run_in_fork, processor)
        result_futures.append(loop.run_in_executor(executor, processor))

    annotated = []
    for text, result_future in zip(texts, result_futures):
        try:
            annotations = await result_future
            annotations['text'] = text
        except Exception:
            raise
            annotations = "Error"
        annotated.append(annotations)

    return annotated


async def process_texts(writing_data, options=None, mode=RUN_MODES.MULTIPROCESSING):
    '''
    Caching:
    1. Create text hash.
    2. Check if hash exist in cache.
    3. Check if some options are a subset of features_available
        Yes: add the intersection of features_available and options to results
    4. Check if some options are a subset of features_running.
        Yes: a. Wait for features_running to finish.
             b. Update the cache
             c. Add intersection of features_running and Options to results
    5. Check if additional features are required. 
        Yes: a. Collect options not covered till now and add to features_running.
             b. Once finished, update cache and return results.
    '''
    recurring_sleep_time=1 # Time to wait between recurring calls to cache to check if features have finished running 
    results = []
    found_options = set()
    cache = learning_observer.kvs.KVS()
    if options is None:
        options = []
    processor = {
        RUN_MODES.MULTIPROCESSING: process_texts_parallel,
        RUN_MODES.SERIAL: process_texts_serial
    }

    for writing in writing_data:
        text = writing.get('text', '')
        if len(text) == 0:
            continue

        # Creating text hash
        text_hash = 'NLP_CACHE_' + learning_observer.util.secure_hash(text.encode('utf-8'))
        text_cache_data = await cache[text_hash]

        if text_cache_data is None:
            # print("{}: text was not found in cache.".format(asyncio.current_task().get_name()))
            text_cache_data = {}

        if 'features_running' not in text_cache_data:
            features_running = set()
        else:
            features_running = set(json.loads(text_cache_data['features_running']))

        if 'features_available' not in text_cache_data:
            text_cache_data['features_available'] = dict()

        # Check if some options are a subset of features_available
        # print("Features Available: ".format(text_cache_data['features_available'].keys()))
        if text_cache_data['features_available']:
            for feature in set(options).intersection(text_cache_data['features_available'].keys()):
                found_options.add(feature)
            # print("{}: Options that were found in features available: {}".format(asyncio.current_task().get_name(), found_options))
            writing.update(text_cache_data['features_available'])

            # If all options were found
            if found_options == set(options):
                # print("{}: All Options were found. Continuing....".format(asyncio.current_task().get_name()))
                results.append(writing)
                continue

        # Check if some options are a subset of features_running
        # print("{}: Features Running: {}".format(asyncio.current_task().get_name(), features_running))
        # features that are needed but are already running
        not_found = set(options) - found_options
        features_needed_running = set() #Features that are needed but are already processing
        if features_running:
            features_needed_running = not_found.intersection(features_running)
        if len(features_needed_running) > 0:
            # print("{}: Features already processing: {}".format(asyncio.current_task().get_name(), features_needed_running))
            while True:
                # print("\n {}: Waiting for features to finish running.".format(asyncio.current_task().get_name()))
                new_cache = await cache[text_hash]
                if new_cache['stop_time'] != "running":
                    break
                asyncio.sleep(recurring_sleep_time)

            # features_running will be available in features_available after they finish running.
            writing.update(text_cache_data['features_available'])
            found_options = found_options.union(features_needed_running)
            features_needed_running = set()
            # If all options are found
            if found_options == set(options):
                # print("{}: All Options were found. Continuing....".format(asyncio.current_task().get_name()))
                results.append(writing)
                continue
            
        # Add not found options to features_running and update cache        
        # print("{}: Finding the rest of the options: {}".format(asyncio.current_task().get_name(), not_found))
        not_found = set(options) - found_options
        features_running = not_found
        text_cache_data['features_running'] = json.dumps(list(features_running))
        text_cache_data['start_time'] = str(datetime.datetime.now())
        text_cache_data['stop_time'] = "running"
        await cache.set(text_hash, text_cache_data)
        annotated_text = list(await processor[mode]([writing.get("text", "")], list(not_found)))[0]
        asyncio.sleep(10)
        text_cache_data['features_running'] = json.dumps([])
        text_cache_data['stop_time'] = str(datetime.datetime.now())
        if annotated_text != "Error":
            text_cache_data['features_available'].update(annotated_text)
            writing.update(annotated_text)
        await cache.set(text_hash, text_cache_data)
        results.append(writing)

    return results


if __name__ == '__main__':
    import time
    import writing_observer.sample_essays
    # Run over a sample text
    example_texts = writing_observer.sample_essays.SHORT_STORIES
    t1 = time.time()
    results = process_text(example_texts[0])
    t2 = time.time()
    print(json.dumps(results, indent=2))

    # If we want to save some test data, flip this to True
    if False:
        with open("results.json", "w") as fp:
            json.dump(results, fp, indent=2)
    print("==============")
    results2 = asyncio.run(process_texts_parallel(example_texts[0:8]))
    t3 = time.time()
    results3 = asyncio.run(process_texts_serial(example_texts[0:8]))
    t4 = time.time()
    print(results2)
    print("Single time", t2 - t1)
    print("Parallel time", t3 - t2)
    print("Serial time", t4 - t3)
    print("Note that these results are imperfect -- ")
    print("Errors", len([r for r in results2 if r == "Error"]))
    print("Errors", [r if r == "Error" else "--" for r in results2])
