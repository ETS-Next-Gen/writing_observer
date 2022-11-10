'''
This is an interface to AWE_Workbench.
'''

import spacy
import coreferee
import spacytextblob.spacytextblob
import awe_components.components.lexicalFeatures
import awe_components.components.syntaxDiscourseFeats
import awe_components.components.viewpointFeatures
import awe_components.components.lexicalClusters
import awe_components.components.contentSegmentation
import json

import time

import nlp_indicators

def init_nlp():
    '''
    Initialize the spacy pipeline with the AWE components. This takes a while
    to run.
    '''
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
        theFilter = [(indicatorName,[True]),('is_alpha',[True])]
    else:
        theFilter = added_filter
        theFilter.append(('is_alpha',[True]))

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
        [[entry['offset'],entry['length']] \
         for entry \
         in data]

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
            indicator['text'].append(text[int(span[0]):int(span[0])+int(span[1])])

    return indicator


def process_text(nlp, text):
    '''
    This will extract a dictionary of metadata using Paul's AWE Workbench code.
    '''
    doc = nlp(text)
    results = {}

    for indicator in nlp_indicators.SPAN_INDICATORS:
        (label, infoType, select, filterInfo, summaryType) = indicator
        results[select] = outputIndicator(doc, select, infoType, stype=summaryType, text=text, added_filter=filterInfo)
        results[select].update({
            "label": label,
            "type": infoType,
            "name": select,
            "summary_type": summaryType
        })
    return results


if  __name__ == '__main__':
    # Run over a sample text
    results = process_text(nlp, nlp_indicators.EXAMPLE_TEXT_1)
    print(json.dumps(results, indent=2))