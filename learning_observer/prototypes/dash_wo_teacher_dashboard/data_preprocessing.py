'''
Process data output from the AWE workbench into UI friendly data
'''
# package imports
import json
import os
import random
import re
from scipy import stats


def normalize(text):
    text = text.replace('&nbsp;', ' ')
    text = text.replace('  ', ' ')
    text = text.replace(' .', '.')
    text = text.replace(' ,', ',')
    text = text.replace(' ;', ';')
    text = text.replace(' :', ':')
    text = text.replace(' !', '!')
    text = text.replace(' ?', '?')
    text = text.replace(' \'s', '\'s')
    text = text.replace(' \'d', '\'d')
    text = text.replace(' \'ve', '\'ve')
    text = text.replace(' \'ll', '\'ll')
    text = text.replace(' n\'t', 'n\'t')
    text = text.replace(' ’s', '\'s')
    text = text.replace(' ’d', '\'d')
    text = text.replace(' ’ve', '\'ve')
    text = text.replace(' ’ll', '\'ll')
    text = text.replace(' n’t', 'n\'t')
    text = text.replace(' - ', '-')
    text = text.replace('"', '" ')
    text = text.replace(' ”', '”')
    text = text.replace('“ ', '“')
    text = text.replace(' "', '"')
    text = text.replace('  ', ' ')
    text = re.sub(r'" (.*?)" ', r' "\1" ', text)
    return text


cwd = os.getcwd()
data_path = os.path.join(cwd, 'uncommitted', 'kaggle_processed')

overall_jsons = [f for f in os.listdir(data_path) if f.endswith('.masked')]
essays = []
# find the ones with libraries mentioned for set 2
for f in overall_jsons:
    f_path = os.path.join(data_path, f)
    with open(f_path, 'r', encoding='utf-8') as f_obj:
        f_data = f_obj.read()
    essay = f.split(".")[0]
    if 'librar' in f_data and 'computer' not in f_data and f'{essay}.json' in os.listdir(data_path):
        essays.append(f'{essay}.json')

# get sample of essays
sample_jsons = random.sample(essays, 24)

# collect data from jsons
students = []
transition_counts = []
academic_counts = []
argument_counts = []
attribution_counts = []
cites_counts = []
sources_counts = []
for f in sample_jsons:
    f_path = os.path.join(data_path, f)
    with open(f_path, 'r') as f_obj:
        f_data = json.load(f_obj)
    text = normalize(' '.join(f_data['doctokens']))

    highlight_info = {
        'coresentences': [],
        'extendedcoresentences': [],
        'contentsegments': [],
    }
    for i in highlight_info:
        for index, t in enumerate(f_data[i]):
            search_text = normalize(' '.join(f_data['doctokens'][t[0]:t[1]]))
            start = text.index(search_text)
            end = start + len(search_text)
            highlight_info[i].append([start, end])
    student = {
        'id': f,
        'text': {
            'emotionwords': {
                'id': 'emotionwords',
                'value': list(set([f_data['doctokens'][i] for i in f_data['emotionwords']])),
                'label': 'Emotion words'
            },
            'concretedetails': {
                'id': 'concretedetails',
                'value': list(set([f_data['doctokens'][i] for i in f_data['concretedetails']])),
                'label': 'Concrete details'
            },
            'argumentwords': {
                'id': 'argumentwords',
                'value': list(set([f_data['doctokens'][i] for i in f_data['argumentwords']])),
                'label': 'Argument words'
            },
            'transitionwords': {
                'id': 'transitionwords',
                'value': list(f_data['transitionprofile'][2].keys()),
                'label': 'Transitions used'
            },
            'studenttext': {
                'id': 'studenttext',
                'value': text,
                'label': 'Student text'
            }
        },
        'highlight': {
            'coresentences': {
                'id': 'coresentences',
                'value': highlight_info['coresentences'],
                'label': 'Main ideas'
            },
            'extendedcoresentences': {
                'id': 'extendedcoresentences',
                'value': highlight_info['extendedcoresentences'],
                'label': 'Supporting ideas'
            },
            'contentsegments': {
                'id': 'contentsegments',
                'value': highlight_info['contentsegments'],
                'label': 'Argument details'
            }
        },
        'metrics': {
            'sentences': {'id': 'sentences', 'value': len(f_data['sentences']), 'label': ' sentences'},
            'adverbs': {'id': 'adverbs', 'value': len([i for i in f_data['pos'] if i == 'ADV']), 'label': ' adverbs'},
            'adjectives': {'id': 'adjectives', 'value': len([i for i in f_data['pos'] if i == 'ADJ']), 'label': ' adjectives'},
            'quotedwords': {'id': 'quotedwords', 'value': len([i for i in f_data['quotedtext'] if i == 1]), 'label': ' quoted words'},
            'timeontask': {'id': 'timeontask', 'value': random.randint(1, 45), 'label': ' minutes on task'},
            'recentwords': {'id': 'recentwords', 'value': random.randint(1, 100), 'label': ' words in last 5 min.'},
        },
        'indicators': {}
    }
    transition_counts.append(f_data['transitionprofile'][0])

    # this will ignore the blanks and periods/commas
    # TODO fix this, not good to rely on the academics attribtue
    total_words = len([x for x in f_data['academics'] if x == 1 or x == 0])

    academic_counts.append(len([x for x in f_data['academics'] if x == 1]) / total_words)
    argument_counts.append(len(f_data['argumentwords']) / total_words)
    attribution_counts.append(len(f_data['attributions']))
    cites_counts.append(len([i for i in f_data['cites'] if i]))
    sources_counts.append(len(f_data['sources']))
    students.append(student)

# collect indicator information (percentiles)
for i, s in enumerate(students):
    s['indicators']['transitions'] = {
        'id': 'transitions',
        'value': int(stats.percentileofscore(transition_counts, transition_counts[i])),
        'label': 'Transitions',
        'help': 'Percentile based on total number of transitions used'
    }
    s['indicators']['academiclanguage'] = {
        'id': 'academiclanguage',
        'value': int(stats.percentileofscore(academic_counts, academic_counts[i])),
        'label': 'Academic Language',
        'help': 'Percentile based on percent of academic language used'
    }
    s['indicators']['argumentlanguage'] = {
        'id': 'argumentlanguage',
        'value': int(stats.percentileofscore(argument_counts, argument_counts[i])),
        'label': 'Argument Language',
        'help': 'Percentile based on percent of argument words used'
    }
    s['indicators']['attributions'] = {
        'id': 'attributions',
        'value': int(stats.percentileofscore(argument_counts, argument_counts[i])),
        'label': 'Attributions',
        'help': 'Percentile based on total attributes'
    }
    s['indicators']['cites'] = {
        'id': 'cites',
        'value': int(stats.percentileofscore(cites_counts, cites_counts[i])),
        'label': 'Citations',
        'help': 'Percentile based on total citations'
    }
    s['indicators']['sources'] = {
        'id': 'sources',
        'value': int(stats.percentileofscore(sources_counts, sources_counts[i])),
        'label': 'Sources',
        'help': 'Percentile based on total sources'
    }

with open(os.path.join(cwd, 'uncommitted', 'sample.json'), 'w') as f:
    json.dump(students, f, indent=4)
